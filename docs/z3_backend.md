# Experimental Z3 backend: benchmark-gated integration

This adapter is an **opt-in alternative for `challenge()`** in PYTHEN 2. It is **not** a replacement for the default Python `evaluate()` semantics and is **not** selected automatically. No change to required dependencies.

## Engines and installation

Two solver adapters are provided, resolved by `engine='auto'` (the default):

1. **`z3py` (preferred)** — the official Z3 Python bindings, driving the `Optimize` API. Install with `pip install "pythen[z3]"` (pulls `z3-solver>=4.8.15`).
2. **`ctypes` (fallback)** — a system `libz3` shared library called through `Z3_eval_smtlib2_string`. **Version support:** the library's SMT-LIB text evaluator must accept optimization commands (`minimize`). Verified working on **Z3 5.x** (validated with 5.4.1). **Not supported:** the Ubuntu/Debian apt `libz3` **4.8.x** (e.g. `libz3.so.4` 4.8.12 on Ubuntu 24.04), which answers `unsupported` to `(minimize ...)` through this entry point even though the CLI supports it.

At load time the ctypes adapter runs a one-shot **capability probe** (a two-variable `minimize` query). If the library fails the probe — or is not found — it raises a `RuntimeError` naming the detected version and pointing to `pip install "pythen[z3]"`, instead of failing later with an opaque "unexpected Z3 output" error mid-query. Pass `engine='z3py'` or `engine='ctypes'` to `Z3ChallengeAnalyzer` to force one.

## Usage

```python
from pythen import Reasoner, Z3ChallengeAnalyzer

rules = [
    {"p": "voidable", "op": "ALL", "conditions": ["minor"], "exceptions": ["necessity"]},
    {"p": "necessity", "op": "ALL", "conditions": ["essential", "fair_price"], "exceptions": []},
]
r = Reasoner(rules, ["minor"])
r.register(Z3ChallengeAnalyzer())          # auto: z3py if installed, else system libz3
a = r.analyze("voidable", method="z3_challenge")
assert (a.radius, a.witness) == (2, ("essential", "fair_price"))
assert r.verify(a).valid
assert a.metadata["engine"] in ("z3py", "ctypes-libz3")

# Use the Python reference on short/easy queries.
b = r.challenge("voidable")
assert b.radius == a.radius
```

## Semantics and correctness

Both engines encode each acyclic rule head as the same Boolean equivalence: `p <-> (OP(conditions) AND NOT ANY(exceptions))`. All present leaf facts are asserted true, missing noncandidate facts false, missing candidate facts are Boolean decision variables, and an opposite target verdict is asserted. Minimizing `SUM(ite(candidate,1,0))` finds the smallest addition-only witness (via the `Optimize` API on z3py, via `(minimize ...)` on the text evaluator). A Python reference evaluation checks that the returned witness actually flips the verdict. A verified optimum follows from SMT Optimize reporting `sat` with an optimal model; `Z3Experiment.prove_no_smaller(...)` can additionally ask the solver to prove that no smaller witness exists (`unsat` at `radius - 1`), and the independent exhaustive verifier can check minimality on small cases.

The backend preserves `flipped`, `stable`, and `budget_exceeded` statuses, including legacy bounded-search reporting. Cycles remain disallowed in `RuleGraph`. The adapter is not a general-purpose ASP or Prolog interpreter, and it does not model epistemic uncertainty or infer conflicting negative facts.

Because the two adapters keep parallel encoders (SMT-LIB text vs AST), the differential test battery runs against **both** engines (`Z3BackendTests` on auto, `Z3CtypesBackendTests` on forced ctypes) plus the Python reference oracle; `bench_z3.py --engine` can revalidate at benchmark scale on either adapter.

## Benchmark and gating

`PYTHONPATH=. python benchmarks/bench_z3.py --random 500 --output /tmp/z3_pythen_results [--engine auto|z3py|ctypes]`

The initial controlled run used a Linux environment with a loadable `libz3` supporting SMT-LIB optimization via ctypes. It passed **2,000 property checks** of status/radius/verdict over 500 generated acyclic rule graphs and four search budgets. All named timing workloads were compared with identical inputs. CSV: `benchmarks/results/z3_gate_2026-11-23.csv`. The follow-up (2026-11-23) reproduced the checks on **Z3 5.4.1** with both engines and fixed the environment reporting; see `docs/performance_gate_2026-11-23.md`.

Main observation: Python is approximately 400-600x faster on simple one-shot `evaluate()` queries; Z3 acceleration becomes substantial on harder `challenge()` workloads (e.g., around 30x at 30 candidate facts/radius 5, and 149x for a stable example with 17 candidates). **Easy radius-1 queries are much slower in Z3.** Therefore the optional Z3 adapter is not a new default engine. Timings are machine- and workload-specific, not universal speed guarantees.

## Operational limitations

- **Supported library versions:** the ctypes text-evaluator path requires Z3 whose SMT-LIB frontend supports `minimize` (verified 5.x). apt `libz3` 4.8.x on Ubuntu/Debian is rejected by the capability probe with an actionable error. `pip install "pythen[z3]"` is the portable route on all platforms.
- SMT optimization is exact when the solver returns a proved optimal `sat` result; `unknown` and timeout raise errors, never return fabricated guarantees.
- Solver output model is a single minimum witness, not necessarily the lexicographically first. Equal-sized alternative witnesses are possible (and may differ between engines); status and `radius` are the stable outputs.
- `AnalysisResult.evaluations` is a reference-evaluator count, **not** a solver instruction count. Use `metadata.solver_invocations`, `metadata.engine`, `metadata.z3_version`, and elapsed wall time for solver comparison.
- `Reasoner.verify(result)` performs an independent exhaustive check by default; it may be exponential on large examples. Pass `verify_optimality=False` to check witness validity only, without claiming an independently verified optimum.
