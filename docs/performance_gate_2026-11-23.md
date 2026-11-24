# Z3 performance gate - 2026-11-23

## Decision

**Conditional integration only.** Keep the original pure-Python `RuleGraph.evaluate()` and `ChallengeAnalyzer` default. Provide a separate, explicitly registered `Z3ChallengeAnalyzer` for selected difficult counterfactual/minimum-witness queries. Do not claim a universal speedup or replace the core evaluation engine.

## Environment

- Linux Python environment with system `libz3.so.4`, called via Python `ctypes`.
- The normal `z3-solver` Python package was unavailable to install because the environment could not access PyPI; this run therefore tests the actual native Z3 optimizer, but not a packaged `z3py` wheel on Windows/macOS.
- No additional mandatory package dependencies.
- Reference: Python `RuleGraph.evaluate()` and brute-force `ChallengeAnalyzer.analyze()` from the public PYTHEN 2 snapshot.
- Benchmark timings include graph-to-SMT encoding, Z3 context creation, optimization, and parsing.

## Correctness gate

- **500 seeded generated acyclic graphs** with **four search budgets** (`None`, 0, 1, 2) each: **2,000 differential challenge comparisons**. Outcomes, radii, and original verdicts matched Python reference on every comparison.
- **47/47 unit tests pass** in the integrated candidate repository. The Z3-specific suite covers nested exceptions, shared dependencies, empty conditions, facts shadowed by rule heads, constrained candidate sets, bounds, and randomly generated rules.
- For exact witnesses, the reference engine evaluates the returned intervention to check that it flips the verdict. For targeted cases, an independent Z3 query with an upper-bound `radius - 1` returned `unsat`.
- Stress tested exact radii of 8 over constructed graphs with **128, 256, 512, and 1,024 candidate facts**. All witnesses flip the verdict and smaller-than-8 interventions are UNSAT under the exact encoding.
- These tests are evidence of correctness on covered cases, not a mathematical proof that the native wrapper is bug-free on every possible input.

## Performance results

Sample medians from this machine (milliseconds). If measured only once, the figure is one run, not a median across runs.

| Workload | Python reference | Z3 adapter | Observed ratio Python/Z3 |
|---|---:|---:|---:|
| Easy radius 1, 32 candidates | 0.0356 | 2.8035 | 0.013x |
| Easy radius 1, 128 candidates | 0.0843 | 5.3688 | 0.016x |
| Radius 4, 22 candidates | 4.9161 | 2.2878 | 2.15x |
| Radius 5, 30 candidates (one run) | 103.1268 | 3.4835 | 29.60x |
| Stable, 14 candidates | 43.1086 | 2.0378 | 21.16x |
| Stable, 17 candidates (one run) | 341.974 | 2.2932 | 149.13x |
| Bounded, 80 candidates / max_changes=3 (one run) | 222.736 | 3.8316 | 58.13x |
| Simple evaluate, 32 candidates (mean of 60 calls) | 0.00338 | 1.55129 | 0.0022x |

The Z3 backend can be several orders of magnitude **slower** for easy queries. It improves difficult brute-force `challenge` instances where most combinations would otherwise be explored. The timings are synthetic and cannot establish production workload distributions.

## Scope and interpretation

The Z3 experiment encodes the existing closed-world, Boolean, acyclic semantics. SAT/SMT does not change burden-of-proof or non-monotonic legal semantics. Solver optimization is an **implementation backend**, not a new reasoning theory by itself.

## Unresolved before default engine selection

- Test the supported `z3-solver` Python package and packaging across Windows/macOS/Linux, pin a known compatible version, validate native library discovery, and benchmark on multiple hardware/OS configurations.
- Exercise memory use, timeouts, error-handling, and deeply nested/shared rule graphs at production scale.
- Benchmark real legal rule sets and realistic question distributions; synthetic speedups on selected hard cases alone do not justify automatic dispatch.
- Independently compare alternative solver backends if needed (PySAT, clingo) using the same semantics and test suite.

The integration is explicitly opt-in and does not alter the published Python evaluation path.

## Follow-up: reproducibility fix (candidate 0.2.0a2)

Release validation of this gate (2026-11-23) on stock **Ubuntu 24.04 with the apt `libz3` 4.8.12** (`libz3.so.4`) **did not reproduce**: that build's `Z3_eval_smtlib2_string` text evaluator answers `unsupported` to `(minimize ...)` even though the CLI supports it, so the original ctypes adapter failed all 11 Z3 tests with "unexpected Z3 output" while the core suite passed. The gate's "system `libz3.so.4`" environment line was therefore not a portable statement of record; it evidently described a newer library exposing the `.so.4` name or an equivalent-capable build.

Changes made in response, all revalidated on **Z3 5.4.1**:

1. **Capability probe:** `NativeZ3` now queries `Z3_get_version` and runs a two-variable `minimize` probe at load time, raising an actionable `RuntimeError` (naming the detected version and recommending `pip install "pythen[z3]"`) instead of failing mid-query. apt `libz3` 4.8.x is explicitly rejected for the ctypes path.
2. **Hybrid engines:** `Z3Experiment`/`Z3ChallengeAnalyzer` prefer the official **z3py `Optimize` API** (the first unresolved item above) and fall back to ctypes; `engine='auto'|'z3py'|'ctypes'` is selectable and reported in `AnalysisResult.metadata.engine` / `z3_version`. `setup.py` gains `extras_require={'z3': ['z3-solver>=4.8.15']}`.
3. **Differential coverage per engine:** the test battery runs against auto and forced-ctypes (`Z3BackendTests`, `Z3CtypesBackendTests`); engines unavailable or failing the probe on the host skip with a reason. Full suite: **60 tests**, plus an interface test asserting the unsupported-library error message.
4. **Benchmark revalidation:** `benchmarks/bench_z3.py --engine z3py|ctypes --random 500` — **2,000/2,000 differential checks pass on each engine**. Headline timings on this follow-up machine (medians, ms; CSVs in `benchmarks/results/followup_2026-11-23_{z3py,ctypes}/`):

| Workload | Python | z3py | ctypes | Ratio Python/ctypes |
|---|---:|---:|---:|---:|
| Stable, 17 candidates | 590.5 | 3.28 | 4.23 | 139.5x |
| Radius 5, 30 candidates | 144.5 | 8.04 | 7.37 | 19.6x |
| Easy radius 1, 128 candidates | 0.147 | 21.7 | 12.7 | 0.012x |

The relative picture from the original gate is unchanged (Z3 wins on hard `challenge()` instances, loses badly on easy one-shot queries), but the absolute numbers are machine-specific and differ from the first gate run; the follow-up CSVs are the reproducible artifacts for this candidate.

Status of the gate decision after the follow-up: **conditional integration retained**, now with the portable `z3py` primary engine, an explicit supported-version policy, and honest environment reporting.
