"""Verified structural shortcuts for addition-only defeasible challenges.

For a *read-once leaf-dependency* rule expression, compute minimum-cardinality
fact additions bottom-up rather than enumerating subsets. At each node, the
minimum plans for TRUE and FALSE compose using min/sum because the leaf sets
of all sibling subexpressions are disjoint. Exceptions are negative inputs:

    p = OP(conditions) AND NOT OR(exceptions)

Shared leaf dependencies invalidate that independence argument; this analyzer
then delegates to an exact reference backend (Python by default, optionally
Z3). Both paths retain the existing closed-world, acyclic-rule semantics.
"""
from dataclasses import replace
from typing import FrozenSet, Optional, Tuple

from .analysis import Analyzer, AnalysisContext, AnalysisResult
from .challenge import ChallengeAnalyzer


# A None plan denotes an unreachable Boolean value under add-only interventions.
Plan = Optional[FrozenSet[str]]


class SharedLeafDependency(Exception):
    """A structural shortcut cannot safely compose overlapping fact leaves."""


def _key(plan: FrozenSet[str]):
    return len(plan), tuple(sorted(plan))


def _minimum(*plans: Plan) -> Plan:
    feasible = [plan for plan in plans if plan is not None]
    return min(feasible, key=_key) if feasible else None


def _combine(*plans: Plan) -> Plan:
    if any(plan is None for plan in plans):
        return None
    result = frozenset()
    for plan in plans:
        result = result | plan
    return result


class _Leaper:
    """Bottom-up exact min-cost inference; rejects any overlapping sibling leaves."""

    def __init__(self, context: AnalysisContext, candidates: Tuple[str, ...]):
        self.graph = context.graph
        self.facts = context.evidence.facts
        self.options = frozenset(candidates)
        self.memo = {}
        self.nodes_visited = 0

    def solve(self, name):
        if name in self.memo:
            return self.memo[name]
        self.nodes_visited += 1
        node = self.graph.nodes.get(name)
        if node is None:
            # Facts are positive only. Existing facts cannot be removed;
            # missing non-candidate facts cannot be added.
            if name in self.facts:
                result = (frozenset(), None, frozenset((name,)))
            elif name in self.options:
                result = (frozenset((name,)), frozenset(), frozenset((name,)))
            else:
                result = (None, frozenset(), frozenset((name,)))
            self.memo[name] = result
            return result

        children = node.conditions + node.exceptions
        solved = [self.solve(child) for child in children]
        footprint = set()
        for _, _, leaves in solved:
            overlap = footprint.intersection(leaves)
            if overlap:
                raise SharedLeafDependency(
                    'shared leaf dependencies: ' + ', '.join(sorted(overlap)[:5])
                )
            footprint.update(leaves)

        n = len(node.conditions)
        conditions = solved[:n]
        exceptions = solved[n:]
        if node.op == 'ALL':
            body_true = _combine(*(x[0] for x in conditions))
            body_false = _minimum(*(x[1] for x in conditions))
        else:
            body_true = _minimum(*(x[0] for x in conditions))
            body_false = _combine(*(x[1] for x in conditions))

        # The empty conjunction is TRUE; the empty disjunction is FALSE.
        if not conditions:
            if node.op == 'ALL':
                body_true, body_false = frozenset(), None
            else:
                body_true, body_false = None, frozenset()

        exception_true = _minimum(*(x[0] for x in exceptions))
        exception_false = _combine(*(x[1] for x in exceptions))
        # No exceptions means their disjunction is FALSE.
        if not exceptions:
            exception_true, exception_false = None, frozenset()

        true_plan = _combine(body_true, exception_false)
        false_plan = _minimum(body_false, exception_true)
        result = true_plan, false_plan, frozenset(footprint)
        self.memo[name] = result
        return result


class LeapAnalyzer(Analyzer):
    """An exact minimum-addition challenge via verified structural shortcuts.

    `fallback='python'` (the default) always uses the existing exact analyzer
    if a shared dependency makes min-plus composition unsound.
    `fallback='z3'` uses the optional solver and raises if it is unavailable.
    Results expose `metadata['execution_mode']` and `metadata['safe_shortcut']`.
    """

    name = 'leap'

    def analyze(self, context: AnalysisContext, candidates=None,
                max_changes=None, fallback='python', z3_engine='auto',
                z3_timeout_ms=15000) -> AnalysisResult:
        if fallback not in ('python', 'z3'):
            raise ValueError("fallback must be 'python' or 'z3'")
        if max_changes is not None and (type(max_changes) is not int or max_changes < 0):
            raise ValueError('max_changes must be a nonnegative integer or None')
        if not isinstance(z3_timeout_ms, int) or isinstance(z3_timeout_ms, bool) or z3_timeout_ms <= 0:
            raise ValueError('z3_timeout_ms must be a positive integer')

        available = set(context.graph.leaves(context.target)) - context.evidence.facts
        if candidates is not None:
            if isinstance(candidates, (str, bytes)):
                raise ValueError('candidates must be an iterable, not a string')
            try:
                choices = set(candidates)
            except TypeError as exc:
                raise ValueError('candidates must be hashable fact strings') from exc
            if any(not isinstance(x, str) or not x for x in choices):
                raise ValueError('candidates must be nonempty fact strings')
            invalid = choices - available
            if invalid:
                raise ValueError('candidates must be missing reachable leaf facts: ' + repr(sorted(invalid)))
            available = choices
        options = tuple(sorted(available))
        limit = len(options) if max_changes is None else min(max_changes, len(options))
        original = context.evaluate()

        computer = _Leaper(context, options)
        try:
            truth, falsity, _ = computer.solve(context.target)
        except SharedLeafDependency as exc:
            if fallback == 'python':
                base = ChallengeAnalyzer().analyze(context, candidates=options,
                                                  max_changes=max_changes)
                mode = 'fallback_python'
            else:
                from .solvers import Z3ChallengeAnalyzer
                base = Z3ChallengeAnalyzer(engine=z3_engine,
                                           timeout_ms=z3_timeout_ms).analyze(
                                               context, candidates=options,
                                               max_changes=max_changes)
                mode = 'fallback_z3'
            return replace(base, method=self.name,
                           metadata=dict(base.metadata,
                                         execution_mode=mode,
                                         safe_shortcut=False,
                                         fallback_reason=str(exc)))

        # Original verdict is authoritative; the two plans are formal,
        # independent minimum-cardinality constructions for each polarity.
        plan = falsity if original else truth
        if plan is not None and len(plan) <= limit:
            witness = tuple(sorted(plan))
            if context.evaluate(context.evidence.facts.union(witness)) == original:
                raise AssertionError('structural plan failed independent evaluation')
            return AnalysisResult(
                self.name, context.target, original, 'flipped', len(witness),
                witness, options, 2, len(witness), 'optimal',
                {'execution_mode': 'structural_leap', 'safe_shortcut': True,
                 'nodes_visited': computer.nodes_visited, 'algorithm': 'read_once_min_plus',
                 'intervention': 'add_only', 'universe': 'reachable_leaf_facts'},
            )
        # Preserve the budget-sensitive result contract of ChallengeAnalyzer:
        # with a limited query a larger flip is not reported as stable.
        complete = limit == len(options)
        return AnalysisResult(
            self.name, context.target, original,
            'stable' if complete else 'budget_exceeded',
            None, (), options, 1, limit, 'exhaustive' if complete else 'bounded',
            {'execution_mode': 'structural_leap', 'safe_shortcut': True,
             'nodes_visited': computer.nodes_visited, 'algorithm': 'read_once_min_plus',
             'intervention': 'add_only', 'universe': 'reachable_leaf_facts'},
        )
