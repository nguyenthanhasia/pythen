# Verified structural leaps in PYTHEN 2

`LeapAnalyzer` is an **optional query method**, not a replacement for the evaluator.
It computes exact minimum-cardinality *addition-only* counterfactuals under
the same acyclic, closed-world rule semantics as `RuleGraph.evaluate()`.

## Rule semantics and cost algebra

For every rule head `p`, `p = OP(conditions) AND NOT ANY(exceptions)`.
Each absent reachable leaf in the `candidates` set may transition from false
to true at unit cost. Present facts cannot be removed and missing facts not
listed as candidates cannot be changed. No direct assignment to a rule head
is allowed.

The method calculates `cost_true(node)` and `cost_false(node)`, together
with one concrete minimum-addition witness for each reachable polarity:

- To make `AND` true, all children must be true: **sum** their costs.
- To make `AND` false, one false child suffices: **minimum** cost.
- To make `OR` true, one true child suffices: **minimum** cost.
- To make `OR` false, all children must be false: **sum** their costs.
- `NOT` exchanges the target truth polarity of its child.
- Impossible targets have infinite cost; empty conjunction and empty
  disjunction have their ordinary `True` and `False` identities.

The implementation uses sets of actual added leaves rather than only costs;
this gives a directly replayable witness and deterministic tie-breaking.

## Soundness condition: disjoint leaf support

A sum is exact **only if children being composed depend on disjoint leaves**.
The analyzer traverses the reachable rule structure and rejects any repeated
leaf across a rule's condition/exception subexpressions (including repetition
through shared derived rule heads). This is a conservative **read-once leaf
support** criterion. Repeated constants with no leaf dependencies are safe.

For accepted graphs, proof is by structural induction:

1. An input leaf has exact costs `0`, `1`, or infinity under addition-only
   interventions according to its present/candidate/frozen state.
2. For `AND`/`OR` with disjoint support sets, the optimal subplans required
   jointly can be unioned without conflicts, and the sum is attainable.
   A single satisfying or violating child suffices for the alternative case.
3. Exceptions are an `OR` of child predicates whose negation is conjoined
   with the rule body. Apply the same identities and disjointness argument.

Consequently the returned witness is minimum-cardinality for the declared
candidate universe, and the original graph independently reevaluates any
reported flip. **Validity of that replay alone does not establish
minimality**; the induction argument establishes optimality in the supported
fragment. `Reasoner.verify(result)` independently enumerates smaller
candidate sets when requested, at potentially exponential cost.

For overlapping leaf supports, the algebra is **not generally sound**:
`p = x AND NOT x` never becomes true, but a naive independent sum could
miscount an impossible state. `LeapAnalyzer` therefore delegates the whole
query to the exact Python analyzer (or optional Z3) and declares the fallback
in `result.metadata`.

## API

```python
from pythen import Reasoner

reasoner = Reasoner(rules, facts)
answer = reasoner.analyze('target', method='leap')
print(answer.status, answer.radius, answer.witness)
print(answer.metadata['execution_mode'])
# structural_leap | fallback_python | fallback_z3

# Select the exact Z3 fallback on shared dependencies (if available):
answer = reasoner.analyze('target', method='leap', fallback='z3')
```

`candidates` and `max_changes` follow the existing `challenge()` API.
Statuses `flipped`, `stable`, and `budget_exceeded` have the same meaning.
With a bounded query (`max_changes < len(candidates)`), no flip within the
budget is still labeled `budget_exceeded`, even if the structural method
could calculate a larger minimum, to preserve the existing API contract.

The method records an explicit `safe_shortcut` Boolean and
`execution_mode`. **If the result says `fallback_python`, no shortcut was
used**, and worst-case complexity remains exponential. In the structural
fragment, bottom-up composition is polynomial in the input size (with costs
for set construction); no unconditional linear-time or overall speedup claim
is made.

## Testing and benchmarking

```bash
python -m unittest discover -s tests
python benchmarks/bench_leap.py --repeats 5 --output benchmarks/results/leap_local.csv
python examples/leap_v2.py
```

The benchmark covers radius 1, read-once high-radius, read-once stable,
shared-dependency fallback, and bounded wide conjunctions. It measures
full query calls including solver initialization. `z3py` is preferred when
installed, otherwise the optional compatible `libz3` fallback is used.
Benchmark results depend on system and exact workload and do not justify a
blanket claim that Leap is faster than Python or Z3.

## Limits

- A structural shortcut is deliberately *not* used on shared-leaf DAGs.
- Only positive fact **additions** count; no removal or rule mutation.
- The metric counts facts, not real-world cost or likelihood of evidence.
- The method does not implement general inference jumps, new legal semantics,
  full proof certificates, or a universal acceleration scheme.
