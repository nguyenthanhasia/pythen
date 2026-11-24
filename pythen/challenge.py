"""Exact minimum-cardinality addition-only counterfactual inference."""
from itertools import combinations
from typing import Iterable, Optional
from .analysis import Analyzer, AnalysisContext, AnalysisResult


ChallengeResult = AnalysisResult  # stable result interface for the v2 framework


class ChallengeAnalyzer(Analyzer):
    name = "challenge"

    def analyze(self, context: AnalysisContext, candidates: Optional[Iterable[str]] = None,
                max_changes: Optional[int] = None) -> AnalysisResult:
        if max_changes is not None and (type(max_changes) is not int or max_changes < 0):
            raise ValueError("max_changes must be a nonnegative integer or None")
        eligible = set(context.graph.leaves(context.target)) - context.evidence.facts
        if candidates is not None:
            if isinstance(candidates, (str, bytes)):
                raise ValueError("candidates must be an iterable, not a string")
            try:
                requested = set(candidates)
            except TypeError as exc:
                raise ValueError("candidates must be hashable fact strings") from exc
            if any(not isinstance(x, str) or not x for x in requested):
                raise ValueError("candidates must be nonempty fact strings")
            invalid = requested - eligible
            if invalid:
                raise ValueError("candidates must be missing reachable leaf facts: " + repr(sorted(invalid)))
            eligible = requested
        options = tuple(sorted(eligible))
        limit = len(options) if max_changes is None else min(max_changes, len(options))
        original = context.evaluate()
        checks = 1
        for size in range(1, limit + 1):
            for added in combinations(options, size):
                checks += 1
                if context.evaluate(context.evidence.facts.union(added)) != original:
                    return AnalysisResult(
                        self.name, context.target, original, "flipped", size, added,
                        options, checks, size, "optimal",
                        {"intervention": "add_only", "universe": "reachable_leaf_facts"},
                    )
        return AnalysisResult(
            self.name, context.target, original,
            "stable" if limit == len(options) else "budget_exceeded",
            None, (), options, checks, limit,
            "exhaustive" if limit == len(options) else "bounded",
            {"intervention": "add_only", "universe": "reachable_leaf_facts"},
        )
