"""Immutable evidence states and explicit interventions for research queries."""
from dataclasses import dataclass
from typing import FrozenSet, Iterable


def _facts(values, name):
    if isinstance(values, (str, bytes)):
        raise ValueError(name + " must be an iterable, not a string")
    try:
        items = frozenset(values)
    except TypeError as exc:
        raise ValueError(name + " must contain hashable strings") from exc
    if any(not isinstance(x, str) or not x for x in items):
        raise ValueError(name + " must contain nonempty fact strings")
    return items


@dataclass(frozen=True)
class Intervention:
    """Explicit, reversible world transformation; never mutates caller state."""
    add: FrozenSet[str] = frozenset()
    remove: FrozenSet[str] = frozenset()

    def __post_init__(self):
        add, remove = _facts(self.add, "add"), _facts(self.remove, "remove")
        if add & remove:
            raise ValueError("an intervention cannot add and remove the same fact")
        object.__setattr__(self, "add", add)
        object.__setattr__(self, "remove", remove)


@dataclass(frozen=True)
class EvidenceState:
    facts: FrozenSet[str]

    def __post_init__(self):
        object.__setattr__(self, "facts", _facts(self.facts, "facts"))

    @classmethod
    def from_facts(cls, facts: Iterable[str]):
        return cls(_facts(facts, "facts"))

    def intervene(self, delta: Intervention):
        if not isinstance(delta, Intervention):
            raise TypeError("delta must be an Intervention")
        return EvidenceState((self.facts - delta.remove) | delta.add)
