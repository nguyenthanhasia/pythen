# PYTHEN 2: Inferential Leap engineering gate (24 November 2026)

**Candidate:** `0.2.0a3`; **host:** Linux, Python 3.13.5, compatible
native `libz3` (Z3 4.13.3). Official `z3py` not installed on this host.
**Methods:** exact Python `challenge`, verified structural `leap`, and optional
Z3 `z3_challenge` via compatible `ctypes` library. All methods use the same
`RuleGraph`, evidence state and target within each workload.

## Correctness gate

- **Full staged pre-merge suite (24 November 2026): 115 tests passed, 0 failed, 0 skipped** on Python 3.13.5 with a compatible native libz3. This includes the original PYTHEN v1 tests retained by the repository, plus v2 and compatibility regressions. It was run on the assembled working tree; it is not yet a GitHub Actions result. The earlier standalone R3 ZIP had only 73 tests (72 pass, 1 skip); that number does **not** describe the uploaded Git branch.
- Independent differential checks inside this suite: **600 seeded random
  DAGs**, **400 seeded read-once trees**, plus **60 seeded random
  Python/Leap/Z3 triple comparisons**.
- Witness, status, radius, budget depth and minimum cardinality agree with
  Python exact search on tested finite cases. Z3 may return a different but
  equally optimal witness; the triple check compares status and radius.
- An overlapping leaf such as `p = x AND NOT x` is never sent to the
  independent-branch shortcut; `LeapAnalyzer` advertises its exact fallback.
- A separate 1,024-leaf conjunction stress test computes a radius of 1,024,
  with a valid witness, in structural mode. An exhaustive verifier of
  minimality is **not** run at that size.

## Latency microbenchmarks

The values below are **20-run medians** of full calls to the public query API,
in milliseconds (lower is better). The rule graphs are constructed outside the
timed region. Z3 analyzer registration is performed once, but the existing R2
Z3 implementation **creates and capability-probes a fresh solver for every
query**. The other methods also execute a fresh query each time.

| Scenario | Python | Leap | Z3 | Leap mode |
| --- | ---: | ---: | ---: | --- |
| Easy, radius 1 (3 leaves) | **0.0077** | 0.0145 | 11.4890 | structural_leap |
| Read-once OR-of-ANDs (25 leaves, radius 5) | 73.5411 | **0.0588** | 5.1170 | structural_leap |
| Read-once stable (16 leaves plus constant TRUE) | 156.9185 | **0.0252** | 4.0503 | structural_leap |
| Shared dependency (same leaf in condition and exception) | **0.0074** | 0.0163 | 3.9453 | fallback_python |
| Wide conjunction (128 leaves, max_changes=2) | 13.9415 | **0.1858** | 5.5836 | structural_leap |

Observed illustrative ratios:

- On the 25-leaf high-radius construction, Python / Leap is approximately
  **1,250x** on this host, and Z3 / Leap approximately **87x**.
- On the 16-leaf stable construction, Python / Leap is approximately
  **6,200x**, and Z3 / Leap approximately **160x**.
- On an easy radius-1 query and a shared-dependency query, **Python wins**.
- Numbers are **not** a generalizable performance guarantee, and should
  not be interpreted as an algorithmic complexity result for arbitrary DAGs.

The [raw 20-run medians, min/max data, graph hashes, and method metadata](../benchmarks/results/leap_20runs.csv)
are shipped in the repository. To reproduce after `pip install -e .`:

```bash
python -m unittest discover -s tests
python benchmarks/bench_leap.py --repeats 20 --output benchmarks/results/leap_20runs_reproduced.csv
```

## Integration decision and limits

**Accept as an opt-in analysis method; do not replace the Python evaluator.**

- The structural shortcut is exact *when it accepts the structure* by
  leaf-disjointness and all input assumptions hold.
- For shared-leaf DAGs, fallback to exact Python or explicitly chosen Z3.
- The default `Reasoner.challenge()` and `RuleTreeEvaluator` are unchanged.
- Extending the shortcut to more general DAGs would require a different proof
  obligation; this integration does not claim to solve that general problem.
- Windows/macOS and the official z3py adapter have not been revalidated in
  this particular benchmark run.
