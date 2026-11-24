"""Stable public facade for the extensible PYTHEN v2 reasoning platform."""
from typing import Iterable, Optional

from .analysis import AnalysisContext, AnalysisResult, Analyzer
from .challenge import ChallengeAnalyzer
from .graph import RuleGraph
from .intervention import EvidenceState, Intervention
from .leap import LeapAnalyzer
from .verification import verify_challenge


class Reasoner:
    """A state plus an immutable rule graph and pluggable research methods.

    `RuleTreeEvaluator` remains available for legacy users; this class is the
    research API. All interventions produce new Reasoner instances.
    """

    def __init__(self, rules, facts=()):
        self.graph = rules if isinstance(rules, RuleGraph) else RuleGraph(rules)
        self.evidence = facts if isinstance(facts, EvidenceState) else EvidenceState.from_facts(facts)
        self._analyzers = {"challenge": ChallengeAnalyzer(), "leap": LeapAnalyzer()}

    @property
    def facts(self):
        return self.evidence.facts

    def register(self, analyzer: Analyzer):
        if not isinstance(analyzer, Analyzer) or not isinstance(analyzer.name, str) or not analyzer.name:
            raise ValueError("analyzer must be a named Analyzer instance")
        if analyzer.name in self._analyzers:
            raise ValueError("analyzer already registered: " + analyzer.name)
        self._analyzers[analyzer.name] = analyzer
        return self

    def context(self, target: str) -> AnalysisContext:
        if not isinstance(target, str) or not target:
            raise ValueError("target must be a nonempty predicate")
        return AnalysisContext(self.graph, self.evidence, target)

    def evaluate(self, target: str) -> bool:
        return self.context(target).evaluate()

    def analyze(self, target: str, method: str = "challenge", **params) -> AnalysisResult:
        if method not in self._analyzers:
            raise ValueError("unknown research method: " + repr(method))
        result = self._analyzers[method].analyze(self.context(target), **params)
        if not isinstance(result, AnalysisResult):
            raise TypeError("analyzer must return AnalysisResult")
        return result

    def challenge(self, target: str, *, candidates: Optional[Iterable[str]] = None,
                  max_changes: Optional[int] = None) -> AnalysisResult:
        return self.analyze(target, method="challenge", candidates=candidates,
                            max_changes=max_changes)

    def verify(self, result: AnalysisResult, **kwargs):
        if result.method not in ("challenge", "z3_challenge", "leap"):
            raise ValueError("no verifier registered for method " + result.method)
        return verify_challenge(self.context(result.target), result, **kwargs)

    def intervene(self, delta: Intervention):
        if not isinstance(delta, Intervention):
            raise TypeError("delta must be an Intervention")
        shadowed = (delta.add | delta.remove) & set(self.graph.nodes)
        if shadowed:
            raise ValueError("cannot directly intervene on derived rule heads: " + repr(sorted(shadowed)))
        next_reasoner = Reasoner(self.graph, self.evidence.intervene(delta))
        next_reasoner._analyzers = dict(self._analyzers)
        return next_reasoner

    def with_facts(self, facts: Iterable[str]):
        next_reasoner = Reasoner(self.graph, facts)
        next_reasoner._analyzers = dict(self._analyzers)
        return next_reasoner
