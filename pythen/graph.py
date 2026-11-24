"""Immutable, acyclic, exception-aware representation of PYTHEN rules.

Semantics on complete *positive fact sets* match PYTHEN v1's RuleTreeEvaluator:
    p = op(conditions) AND NOT any(exceptions)
Unlisted leaf facts are false under the v1 closed-world convention.
"""
from dataclasses import dataclass
from hashlib import sha256
import json
from types import MappingProxyType
from typing import Dict, Iterable, Mapping, Optional, Tuple


@dataclass(frozen=True)
class RuleNode:
    name: str
    op: str
    conditions: Tuple[str, ...]
    exceptions: Tuple[str, ...]


class RuleGraph:
    """Frozen rule DAG; rejects cycles and duplicate rule heads.

    The source list is copied and never modified. Sharing subpropositions is fine.
    A rule head supplied as a fact is ignored, matching v1 semantics.
    """

    def __init__(self, rules: Iterable[dict]):
        if isinstance(rules, (str, bytes)):
            raise ValueError("rules must be an iterable of rule dictionaries")
        nodes: Dict[str, RuleNode] = {}
        for item in rules:
            if not isinstance(item, dict):
                raise ValueError("each rule must be a dictionary")
            name = item.get("p")
            if not isinstance(name, str) or not name:
                raise ValueError("rule 'p' must be a nonempty string")
            if name in nodes:
                raise ValueError("duplicate rule head: " + name)
            op = item.get("op")
            if op not in ("ALL", "AND", "ANY", "OR"):
                raise ValueError("invalid operator for " + name)
            conditions = item.get("conditions")
            exceptions = item.get("exceptions", ())
            if not isinstance(conditions, (list, tuple)) or not isinstance(exceptions, (list, tuple)):
                raise ValueError("conditions and exceptions must be sequences")
            if any(not isinstance(x, str) or not x for x in list(conditions) + list(exceptions)):
                raise ValueError("conditions must be nonempty predicate strings")
            if any(not isinstance(x, str) or not x for x in exceptions):
                raise ValueError("exceptions must be nonempty predicate strings")
            nodes[name] = RuleNode(
                name, "ALL" if op in ("ALL", "AND") else "ANY",
                tuple(conditions), tuple(exceptions),
            )
        if not nodes:
            raise ValueError("rule set must not be empty")
        active, done = set(), set()

        def visit(name):
            if name not in nodes or name in done:
                return
            if name in active:
                raise ValueError("Cyclic rule dependency at " + name)
            active.add(name)
            node = nodes[name]
            for child in node.conditions + node.exceptions:
                visit(child)
            active.remove(name)
            done.add(name)

        for name in nodes:
            visit(name)
        self._nodes: Mapping[str, RuleNode] = MappingProxyType(nodes)
        self._json = tuple({
            "p": node.name, "op": node.op, "conditions": list(node.conditions),
            "exceptions": list(node.exceptions),
        } for node in sorted(nodes.values(), key=lambda item: item.name))
        payload = json.dumps(self._json, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        self._fingerprint = sha256(payload.encode("utf-8")).hexdigest()

    @property
    def nodes(self) -> Mapping[str, RuleNode]:
        return self._nodes

    @property
    def fingerprint(self) -> str:
        return self._fingerprint

    def to_rules(self) -> Tuple[dict, ...]:
        """Return defensive copies of the normalized rule source."""
        return tuple({
            "p": x["p"], "op": x["op"],
            "conditions": list(x["conditions"]), "exceptions": list(x["exceptions"]),
        } for x in self._json)

    def leaves(self, target: Optional[str] = None) -> Tuple[str, ...]:
        """Return reachable leaf predicates (or all leaves when target is None)."""
        found, seen = set(), set()

        def walk(name):
            if name in seen:
                return
            seen.add(name)
            node = self._nodes.get(name)
            if node is None:
                found.add(name)
            else:
                for child in node.conditions + node.exceptions:
                    walk(child)

        if target is None:
            for name in self._nodes:
                walk(name)
        else:
            if not isinstance(target, str) or not target:
                raise ValueError("target must be a nonempty predicate name")
            walk(target)
        return tuple(sorted(found))

    def evaluate(self, facts: Iterable[str], target: str) -> bool:
        """Pure v1-compatible Boolean evaluation, with memoization for a DAG."""
        if not isinstance(target, str) or not target:
            raise ValueError("target must be a nonempty predicate name")
        if isinstance(facts, (str, bytes)):
            raise ValueError("facts must be a collection of strings")
        known = frozenset(facts)
        if any(not isinstance(x, str) for x in known):
            raise ValueError("facts must contain strings")
        memo = {}

        def eval_node(name):
            if name in memo:
                return memo[name]
            node = self._nodes.get(name)
            if node is None:
                result = name in known
            else:
                # Equivalent to v1: exception-first, ALL/ANY, including empty lists.
                defeated = any(eval_node(x) for x in node.exceptions)
                if defeated:
                    result = False
                elif node.op == "ALL":
                    result = all(eval_node(x) for x in node.conditions)
                else:
                    result = any(eval_node(x) for x in node.conditions)
            memo[name] = result
            return result

        return eval_node(target)
