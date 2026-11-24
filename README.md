# PYTHEN 2

**An extensible Python framework for verifiable defeasible reasoning.**

PYTHEN 2 builds on the original [PYTHEN](https://github.com/nguyenthanhasia/pythen) rule evaluator. It keeps the readable `ALL` / `ANY` / `exceptions` syntax while introducing immutable reasoning states, pluggable analyses, explicit verification, and an optional Z3 backend for computationally difficult counterfactual queries.

**Status:** Research preview `0.2.0a3`. This source snapshot is not yet merged into the original repository or published as a PYTHEN 2 release on PyPI.

## What's new in PYTHEN 2?

| Capability | What it provides |
| --- | --- |
| **Reusable reasoning graph** | An immutable, validated rule DAG with shared subpropositions, nested exceptions, and a deterministic SHA-256 fingerprint. |
| **Counterfactual analysis** | `challenge()` finds a smallest set of additional facts that changes a modeled conclusion. |
| **Explicit verification** | `verify()` distinguishes a valid counterexample from a *provably minimum-cardinality* counterexample. |
| **Immutable interventions** | `intervene()` evaluates hypothetical evidence states without changing the original case. |
| **Extensible analysis API** | Researchers can register `Analyzer` implementations without changing the evaluator or rule format. |
| **Verified structural leaps** | `LeapAnalyzer` computes exact minimum-addition witnesses directly for disjoint-leaf rule structures; overlapping dependencies trigger a declared exact fallback. |
| **Optional hybrid solving** | `Z3ChallengeAnalyzer` uses Z3 for selected difficult searches; the fast, dependency-free Python engine remains the default. |
| **Reproducible results** | Normalized rule exports, experiment records, benchmark scripts, and differential tests support repeatable comparisons. |

## Install

Requires Python 3.7 or later. The standard reasoning engine has **no third-party runtime dependencies**.

From the extracted source directory:

```bash
python -m pip install -e .
```

To use the optional Z3 backend, install the official Python bindings as well:

```bash
python -m pip install -e '.[z3]'
```

Alternatively, the package can use an already installed system `libz3` through `ctypes` when that library supports the required optimization commands. See [Z3 backend details](docs/z3_backend.md).

## Quickstart: evaluate, challenge, verify

Suppose, in a **simplified hypothetical example**, a contract is voidable when the signer is a minor, unless the goods are essential **and** the price is fair. This rule is for demonstrating the API, not for describing the law of a particular jurisdiction.

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

# 1. Evaluate the current evidence.
print(reasoner.evaluate("contract_voidable"))
# True

# 2. Find a minimum addition-only intervention that flips the verdict.
result = reasoner.challenge("contract_voidable")
print(result.status, result.radius)
# flipped 2
print(result.witness)
# ('goods_are_essential', 'price_is_fair')

# 3. Verify both the flip and minimum cardinality.
check = reasoner.verify(result)
print(check.valid, check.optimal)
# True True

# 4. Inspect the counterfactual without modifying the original facts.
scenario = reasoner.intervene(Intervention(add=result.witness))
print(scenario.evaluate("contract_voidable"))
# False
print(reasoner.evaluate("contract_voidable"))
# True
```

Run the included example:

```bash
python examples/quickstart_v2.py
```

### Understanding `radius` and `witness`

- **Radius**, also exposed as `flip_distance`, is the minimum **number** of currently absent, allowed leaf facts that must be added to change the model's verdict.
- **Witness** is one concrete set of additional facts that achieves this change at the minimum cardinality.

Here the exception requires **two** missing facts. Adding either alone does not change the verdict; adding both does. Thus the radius is `2` and the witness is `('goods_are_essential', 'price_is_fair')`.

This is a **structural counterfactual** over a declared fact universe. It is not a probability, legal prediction, or real-world measure of how difficult evidence is to obtain.

### Understanding the result statuses

| Status | Meaning |
| --- | --- |
| `flipped` | A minimum-cardinality fact addition was found within the declared candidate set. |
| `stable` | No fact addition in that entire candidate set can flip the verdict. |
| `budget_exceeded` | No flip was found within `max_changes`; larger interventions have not been ruled out. |

You can restrict the search with `candidates` and `max_changes`. The default `challenge()` uses an exact, cardinality-ordered search and can require exponential time in the worst case.

## Verified Inferential Leap (optional analyzer)

PYTHEN 2 includes a **Verified Structural Leap** method for exact counterfactual
queries. Where each rule branch depends on a disjoint set of leaf facts, it
computes the minimum fact additions by combining local `min` and `sum` plans
rather than searching fact subsets. It supports nested exceptions under the
existing rule semantics.

```python
# Uses the same rules and evidence as the quickstart above.
leap = reasoner.analyze("contract_voidable", method="leap")
print(leap.radius, leap.witness)
# 2 ('goods_are_essential', 'price_is_fair')
print(leap.metadata["execution_mode"])
# structural_leap
print(reasoner.verify(leap).optimal)
# True
```

If multiple branches depend on the same fact, this shortcut **cannot safely
add their costs**. The method automatically falls back to the exact Python
search, with `execution_mode="fallback_python"` recorded in the result.
Optionally choose Z3 for this fallback:

```python
leap = reasoner.analyze("contract_voidable", method="leap", fallback="z3")
```

The Z3 fallback is only required when the structural shortcut is unsafe;
`fallback="z3"` does not force solver usage on safe read-once graphs. Z3
is an optional installation; if unavailable for a required fallback, an
error is raised rather than silently claiming success.

Leap is **not always faster**: easy cases can be fastest with plain Python.
Read the [structural soundness conditions](docs/leap_backend.md) and [20-run engineering benchmark](docs/leap_benchmark_2026-11-24.md)
for the precise supported fragment and limits.

Run the new example:

```bash
python examples/leap_v2.py
```

## Optional Z3 backend

The Z3 adapter turns the same acyclic Boolean rules into SMT constraints and minimizes the number of added facts needed to reverse the original verdict. It is **opt-in** and does **not** replace `Reasoner.evaluate()` or the default Python `challenge()`.

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

Available solver choices:

- `engine="auto"` (default for the Z3 analyzer): prefer the official `z3py` bindings; otherwise try a compatible system `libz3`.
- `engine="z3py"`: use the official Python bindings and Z3 `Optimize` API.
- `engine="ctypes"`: use a compatible native Z3 library through the SMT-LIB text interface.

For example, force a solver with `Z3ChallengeAnalyzer(engine="z3py")`.

The native adapter checks library capabilities and raises a useful error if its optimization interface is unsupported. Some system distributions of `libz3` 4.8.x are incompatible with this fallback; installing the Python extra above is the recommended setup.

**Performance is workload-dependent.** In the benchmark records shipped with this snapshot, Z3 is considerably faster on certain high-radius or stable `challenge()` instances, but slower on small or easy queries. Z3 is not automatically dispatched for a query, and no universal speedup is claimed. Results, environment data, and the exact benchmark command are available in [the performance report](docs/performance_gate_2026-11-23.md).

For large cases, `reasoner.verify(result, verify_optimality=False)` checks the witness without independently re-running an exhaustive optimality check. In that mode, `check.optimal` is `None`, **not** `True`.

## Architecture

```text
JSON/Python rule dictionaries
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
          /       \
    challenge   leap   z3_challenge (optional)
          \       /
        AnalysisResult
             |
          verify()
```

The `RuleGraph` represents an acyclic set of rule dependencies. `EvidenceState` stores case facts, and `Intervention` produces a new state rather than mutating existing evidence. An `AnalysisResult` records the query, status, witness, search scope, and declared guarantees.

### Add your own analyzer

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

The framework verifies the `AnalysisResult` type but does not automatically certify the correctness of custom analyzers. New methods must establish their own guarantees and tests.

## Semantics and compatibility

For a rule head `p`, the Boolean evaluator implements:

```text
p = OP(conditions) AND NOT ANY(exceptions)
```

`OP` is either `ALL` or `ANY`. An unlisted leaf fact evaluates to `False` (closed-world assumption); `ALL` with no conditions is `True`, while `ANY` with no conditions is `False`. Shared predicates are supported. Cyclic rule dependencies are rejected.

The original `RuleTreeEvaluator` remains available for existing PYTHEN code. On acyclic rule sets, the new `RuleGraph` preserves the original Boolean rule-evaluation behavior. PYTHEN 2 does not introduce probabilistic evidence, three-valued epistemic logic, or legal proof standards.

See [Framework semantics](docs/framework_v2.md) for the precise query and verification contracts.

## Tests and reproducibility

```bash
python -m unittest discover -s tests
```

In the local Linux environment used to review this R3 snapshot, **73 tests ran, 72 passed, and 1 was skipped** (including 1,000 randomized Python/Leap and 60 three-way Python/Leap/Z3 differential cases). This checks the framework API and an available native Z3 path, but does not establish platform-wide compatibility with every Z3 build. The archive also contains separate benchmark records from prior z3py and ctypes runs; those records are not a substitute for reproducing the measurements in a target environment.

To run a three-way comparison on the specified microbenchmarks, first install the package and then execute:

```bash
python benchmarks/bench_leap.py --repeats 5 --output benchmarks/results/leap_local.csv
```

For the Z3-specific randomized differential comparisons:

```bash
python benchmarks/bench_z3.py --engine auto --random 500 --output benchmark-output
```

The benchmark compares status, minimum radius, and baseline verdict against the Python reference evaluator. Its output includes an audit JSON and CSV, with the environment and observed solver version. Test cases and performance records are in [`tests/`](tests/) and [`benchmarks/`](benchmarks/).

For a simple reusable experiment record:

```python
from pythen.research import export_experiment

export_experiment("experiment.json", reasoner.graph, reasoner.evidence, result)
```

## License and citation

MIT License. See [LICENSE](LICENSE).

If you use the original PYTHEN framework in research, see Nguyen and Satoh, *PYTHEN: A Flexible Framework for Legal Reasoning in Python* (2026), [arXiv:2603.15317](https://arxiv.org/abs/2603.15317).
