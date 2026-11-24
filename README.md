# PYTHEN 2

**An extensible Python framework for verifiable defeasible reasoning.**

[![PyPI](https://img.shields.io/pypi/v/pythen.svg)](https://pypi.org/project/pythen/)
[![Python](https://img.shields.io/pypi/pyversions/pythen.svg)](https://pypi.org/project/pythen/)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](https://github.com/nguyenthanhasia/pythen/blob/main/LICENSE)

PYTHEN 2 builds on the original [PYTHEN](https://github.com/nguyenthanhasia/pythen) rule evaluator. It retains the readable `ALL` / `ANY` / `exceptions` syntax and adds immutable reasoning states, pluggable analyzers, counterfactual reasoning, explicit verification, and optional Z3 solving.

**Current release:** [0.2.0a3 on PyPI](https://pypi.org/project/pythen/0.2.0a3/) | [GitHub release v0.2.0a3](https://github.com/nguyenthanhasia/pythen/releases/tag/v0.2.0a3)

**Status:** Published alpha research preview. This is not a stable API release. The original PYTHEN v1 interface remains available.

## Highlights

| Capability | What it provides |
| --- | --- |
| **Reusable reasoning graph** | Immutable, validated rule DAGs with shared subpropositions, nested exceptions, and a deterministic SHA-256 fingerprint. |
| **Counterfactual analysis** | `challenge()` searches for the smallest allowed additions of facts that change a modeled conclusion. |
| **Explicit verification** | `verify()` separates witness validity from minimum-cardinality optimality. |
| **Immutable interventions** | `intervene()` evaluates hypothetical evidence without changing the original case. |
| **Extensible analyzer API** | Researchers can register custom `Analyzer` implementations without modifying the rule evaluator. |
| **Verified structural leaps** | `LeapAnalyzer` uses exact bottom-up computation on supported disjoint-leaf structures and exact fallback elsewhere. |
| **Optional Z3 solving** | `Z3ChallengeAnalyzer` can handle selected counterfactual searches through Z3; the core Python evaluator remains the default. |
| **Reproducibility** | Rule fingerprints, experiment exports, benchmark scripts, and differential tests support repeatable comparisons. |

## Installation

PYTHEN 2 requires Python 3.7 or newer. The core package has no third-party runtime dependencies.

Install the published alpha release:

```bash
python -m pip install "pythen==0.2.0a3"
```

Install with optional Z3 bindings:

```bash
python -m pip install "pythen[z3]==0.2.0a3"
```

For development from source:

```bash
git clone https://github.com/nguyenthanhasia/pythen.git
cd pythen
python -m pip install -e .
```

Z3 can alternatively use a compatible system `libz3` through `ctypes` if the library supports the required optimization interface. See the [Z3 backend documentation](https://github.com/nguyenthanhasia/pythen/blob/main/docs/z3_backend.md).

## Quickstart: evaluate, challenge, verify

Consider a simplified hypothetical rule: a contract is voidable when the signer is a minor, unless the goods are essential **and** the price is fair. This example demonstrates the API, not the law of any specific jurisdiction.

```python
from pythen import Reasoner, Intervention

rules = [
    {
        "p": "contract_voidable",
        "op": "ALL",
        "conditions": ["signer_is_minor"],
        "exceptions": ["necessities_exception"],
    },
    {
        "p": "necessities_exception",
        "op": "ALL",
        "conditions": ["goods_are_essential", "price_is_fair"],
        "exceptions": [],
    },
]

reasoner = Reasoner(rules, facts=["signer_is_minor"])

# Evaluate the current evidence.
print(reasoner.evaluate("contract_voidable"))
# True

# Find a minimum addition-only intervention that flips the verdict.
result = reasoner.challenge("contract_voidable")
print(result.status, result.radius)
# flipped 2
print(result.witness)
# ('goods_are_essential', 'price_is_fair')

# Verify the flip and minimum cardinality.
check = reasoner.verify(result)
print(check.valid, check.optimal)
# True True

# Evaluate a counterfactual without modifying the original evidence.
scenario = reasoner.intervene(Intervention(add=result.witness))
print(scenario.evaluate("contract_voidable"))
# False
print(reasoner.evaluate("contract_voidable"))
# True
```

The source repository also includes an [executable quickstart](https://github.com/nguyenthanhasia/pythen/blob/main/examples/quickstart_v2.py).

### Radius and witness

- **Radius**, also exposed as `flip_distance`, is the minimum **number** of currently absent, permitted leaf facts that must be added to change the modeled verdict.
- **Witness** is one concrete minimum-cardinality set of fact additions that causes the change.

In the example, the exception requires two missing facts. Neither addition alone changes the verdict, but adding both does. Therefore the radius is `2`.

These are **structural counterfactuals** within a declared fact universe. They are not probabilities, forecasts of legal outcomes, or measures of the real-world difficulty of obtaining evidence.

### Result statuses

| Status | Meaning |
| --- | --- |
| `flipped` | A minimum-cardinality fact addition was found in the declared candidate set. |
| `stable` | No addition from the complete candidate set can flip the verdict. |
| `budget_exceeded` | No flip was found within `max_changes`; larger interventions remain possible. |

Use `candidates` and `max_changes` to constrain a search. The default `challenge()` performs exact cardinality-ordered search, which may take exponential time in the worst case.

## Verified Inferential Leap

PYTHEN 2 includes an optional **Verified Structural Leap** analyzer for minimum-addition counterfactual queries. On rule structures whose branches have disjoint leaf dependencies, it calculates the minimum intervention cost directly using bottom-up `min` and `sum` computations instead of enumerating fact subsets. Nested exceptions are supported under the existing rule semantics.

```python
# Continuing from the quickstart above.
leap = reasoner.analyze("contract_voidable", method="leap")
print(leap.radius, leap.witness)
# 2 ('goods_are_essential', 'price_is_fair')
print(leap.metadata["execution_mode"])
# structural_leap
print(reasoner.verify(leap).optimal)
# True
```

Independently combining the costs of branches that share facts can yield an invalid plan. To preserve exactness, the analyzer detects unsupported shared-leaf dependencies and falls back to the exact Python search, recording `execution_mode="fallback_python"`.

An explicit Z3 fallback is also available:

```python
leap = reasoner.analyze("contract_voidable", method="leap", fallback="z3")
```

This setting does not force Z3 on a supported structural case. If a Z3 fallback is required but no usable engine is installed, PYTHEN raises an error instead of claiming success.

The shortcut is **not universally faster** than exact Python search. Read the [soundness conditions](https://github.com/nguyenthanhasia/pythen/blob/main/docs/leap_backend.md), [engineering benchmark](https://github.com/nguyenthanhasia/pythen/blob/main/docs/leap_benchmark_2026-11-24.md), and [runnable example](https://github.com/nguyenthanhasia/pythen/blob/main/examples/leap_v2.py) for the supported fragment and measured limits.

## Optional Z3 backend

The Z3 analyzer encodes acyclic Boolean rules as SMT constraints and minimizes the number of additional facts required to reverse the original verdict. It is opt-in; it does not replace `Reasoner.evaluate()` or the default Python `challenge()`.

```python
from pythen import Reasoner, Z3ChallengeAnalyzer

reasoner = Reasoner(rules, facts=["signer_is_minor"])
reasoner.register(Z3ChallengeAnalyzer())

result = reasoner.analyze("contract_voidable", method="z3_challenge")
print(result.radius, result.witness)
# 2 ('goods_are_essential', 'price_is_fair')
print(result.metadata["engine"])
# 'z3py' or 'ctypes-libz3'
```

Supported engines:

- `engine="auto"`: prefer the official `z3py` bindings, then try a compatible system `libz3`.
- `engine="z3py"`: use Z3's official Python bindings and `Optimize` API.
- `engine="ctypes"`: use a compatible native Z3 library through the SMT-LIB text interface.

For example, register `Z3ChallengeAnalyzer(engine="z3py")` to require official Python bindings.

The native adapter checks solver capabilities and provides a diagnostic error if the optimization interface is unavailable. Some system `libz3` 4.8.x builds are incompatible with this fallback. The Python extra is the recommended setup.

**Performance is workload-dependent.** Shipped benchmark records show gains on some high-radius or stable queries and overhead on easy queries. Z3 is not automatically dispatched, and no universal speedup is claimed. See the [performance report](https://github.com/nguyenthanhasia/pythen/blob/main/docs/performance_gate_2026-11-23.md).

For expensive optimality checks, `reasoner.verify(result, verify_optimality=False)` verifies the witness without independently repeating the exact optimality search. In that mode, `check.optimal` is `None`, not `True`.

## Architecture

```text
JSON / Python rule dictionaries
             |
             v
      RuleGraph (immutable)
             |
      EvidenceState (immutable)
             |
          Reasoner
       /      |       \
  evaluate  analyze  intervene
             |
         Analyzer API
        /    |    \
 challenge  leap  z3_challenge (optional)
        \    |    /
        AnalysisResult
             |
          verify()
```

`RuleGraph` stores validated acyclic rule dependencies, `EvidenceState` holds case facts, and `Intervention` creates a hypothetical state without mutating the original. `AnalysisResult` records the query, result status, witness, search scope, and claimed guarantees.

### Implement a custom analyzer

```python
from pythen import Analyzer, AnalysisResult

class LeafCount(Analyzer):
    name = "leaf_count"

    def analyze(self, context, **kwargs):
        return AnalysisResult(
            method=self.name,
            target=context.target,
            original_verdict=context.evaluate(),
            status="complete",
            metadata={
                "reachable_leaves": len(context.graph.leaves(context.target))
            },
        )

reasoner.register(LeafCount())
print(reasoner.analyze("contract_voidable", method="leaf_count").metadata)
```

Registering an analyzer does not automatically certify its correctness. Custom implementations must establish their own assumptions, guarantees, and tests.

## Semantics and compatibility

For rule head `p`, the Boolean evaluator implements:

```text
p = OP(conditions) AND NOT ANY(exceptions)
```

`OP` may be `ALL` or `ANY`. Absent leaf facts evaluate to `False` under the closed-world assumption. `ALL` with an empty condition set is `True`; `ANY` with an empty condition set is `False`. Rule graphs may share predicates, but cyclic dependencies are rejected.

The original `RuleTreeEvaluator` remains available for PYTHEN v1 code. The new graph evaluator preserves Boolean rule evaluation for supported acyclic models. PYTHEN 2 does not implement probabilistic evidence, three-valued epistemic logic, or real-world legal proof standards.

Read the [framework semantics](https://github.com/nguyenthanhasia/pythen/blob/main/docs/framework_v2.md) for query contracts and verification behavior.

## Tests and reproducibility

The GitHub Actions CI for release `v0.2.0a3` passed the core and legacy test suite on Linux with **Python 3.7, 3.8, 3.9, 3.11, and 3.13**. A separate Z3 integration job using official Python bindings on Python 3.11 also passed. These results do not establish compatibility with untested interpreter and operating-system combinations.

Run the test suite from a source checkout:

```bash
python -m unittest discover -s tests -v
```

CI logs are available from [GitHub Actions](https://github.com/nguyenthanhasia/pythen/actions/workflows/tests.yml). The test suite includes randomized Python/Leap differential tests and comparisons against Z3 when the optional backend is installed; Z3-specific tests may be skipped in environments without Z3.

For the microbenchmark comparison:

```bash
python benchmarks/bench_leap.py --repeats 5 --output benchmarks/results/leap_local.csv
```

For Z3 randomized differential comparisons:

```bash
python benchmarks/bench_z3.py --engine auto --random 500 --output benchmark-output
```

Benchmarks are workload-specific and do not establish universal speedups. The scripts, environment records, and sample results are available under [benchmarks/](https://github.com/nguyenthanhasia/pythen/tree/main/benchmarks).

Export an experiment record:

```python
from pythen.research import export_experiment

export_experiment("experiment.json", reasoner.graph, reasoner.evidence, result)
```

## License and citation

PYTHEN is released under the [MIT License](https://github.com/nguyenthanhasia/pythen/blob/main/LICENSE).

For research using the original PYTHEN framework, see Nguyen and Satoh (2026), *PYTHEN: A Flexible Framework for Legal Reasoning in Python*, [arXiv:2603.15317](https://arxiv.org/abs/2603.15317).

This alpha preview extends that framework. It is not, by itself, a separately published peer-reviewed description of the new analysis algorithms.
