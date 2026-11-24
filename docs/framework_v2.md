# PYTHEN 2: public semantics and API reference

PYTHEN 2 is a research framework over an acyclic, exception-aware Boolean rule graph. It documents the behavior of the implemented components.

## Rule evaluation

A rule is a mapping with a unique string head `p`, an operator `ALL/AND` or `ANY/OR`, a list of string `conditions`, and an optional list of string `exceptions`. Given an evidence state containing a set of positive facts `F`, a leaf predicate `q` not defined by a rule evaluates to `q in F`. A defined rule head ignores any direct fact with its own name.

```text
E(p, F) = [AND or OR over E(c, F) for conditions c]
          AND NOT [OR over E(e, F) for exceptions e]
```

Empty conjunctions are true and empty disjunctions are false. Shared predicates are evaluated consistently using memoization; cycles are rejected at construction time. All public graph views are defensive copies or frozen structures.

## Counterfactual analysis

Given fixed rule graph G, positive fact set F, target t, and a declared candidate universe U of currently absent, reachable leaf facts, `challenge(t)` returns a witness `D subset U` of minimum cardinality such that `E_G(t, F union D) != E_G(t, F)`, if one exists.

- `radius`: `len(D)` if a flip is found, `None` otherwise.
- `witness`: lexicographically determined minimum-cardinality set.
- `status='flipped'`: exact minimum cardinality found by enumeration.
- `status='stable'`: no flipping addition in the declared universe.
- `status='budget_exceeded'`: no flip at or below `max_changes`; no conclusion about larger sets.

`verify(result)` checks witness validity, then (by default) exhaustive absence of any smaller witness. Both solver and verifier use the same Boolean graph semantics; they run separate enumeration passes, not two independently implemented semantics.

## Verified structural inference

`LeapAnalyzer` is a research method implementing exact minimum-addition
counterfactuals for reachable expressions whose sibling subexpressions have
disjoint leaf support. It computes polarity-specific witness plans using a
min-plus recurrence over Boolean connectives and rule exceptions. On shared
leaf dependencies, it delegates to Python exact search or a selected optional
Z3 backend. Both paths produce ordinary `AnalysisResult`s with an explicit
execution-mode label; the evaluator's semantics and default behavior remain
unchanged. See [Leap analyzer soundness and limitations](leap_backend.md).

## Extension contract

`Analyzer.analyze(context, **params)` returns `AnalysisResult`. The context exposes a frozen rule graph and an immutable evidence state. The framework checks result type, not arbitrary method correctness. External methods must state their own guarantees and implement separate checks as needed.

`Reasoner.intervene(Intervention(add=..., remove=...))` creates a fresh reasoner; the original is unchanged. Direct interventions on derived heads are rejected. `with_facts` creates an alternate state on the same graph.

## Reproducibility

`pythen.research.export_experiment(path, graph, evidence, result)` exports a JSON record with normalized rules, graph SHA256, input facts, query scope, output and guarantee labels. A reproducible record does not constitute a semantic correctness proof.

## Scope

PYTHEN 2 retains the closed-world convention and models rule applicability only. It does not implement three-valued epistemic semantics, legal proof standards, dynamic rule changes, or unrestricted cyclic semantics. Fact cardinality is not the cost of discovering or establishing evidence in a real case.
