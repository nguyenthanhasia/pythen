"""Small extension API for independently developed research methods."""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Mapping, Optional, Tuple

from .graph import RuleGraph
from .intervention import EvidenceState


@dataclass(frozen=True)
class AnalysisContext:
    graph: RuleGraph
    evidence: EvidenceState
    target: str

    def evaluate(self, facts=None) -> bool:
        return self.graph.evaluate(self.evidence.facts if facts is None else facts, self.target)


@dataclass(frozen=True)
class AnalysisResult:
    """Result object with guarantees explicit rather than implied by a witness."""
    method: str
    target: str
    original_verdict: bool
    status: str
    radius: Optional[int] = None
    witness: Tuple[str, ...] = ()
    candidates: Tuple[str, ...] = ()
    evaluations: int = 0
    searched_up_to: int = 0
    guarantee: str = "none"
    metadata: Mapping[str, Any] = field(default_factory=dict)

    @property
    def flip_distance(self):
        return self.radius

    @property
    def counterfactual_verdict(self):
        return (not self.original_verdict) if self.status == "flipped" else None


class Analyzer(ABC):
    """Implement analyze(context, **params) and provide a unique name."""
    name: str = ""

    @abstractmethod
    def analyze(self, context: AnalysisContext, **params) -> AnalysisResult:
        raise NotImplementedError
