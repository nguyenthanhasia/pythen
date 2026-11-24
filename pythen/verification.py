"""Independent witness/optimality checks over the declared candidate universe.

A witness validity check is NOT a proof of minimum cardinality. To verify
optimality, search every smaller intervention. This is exponential in general.
"""
from dataclasses import dataclass
from itertools import combinations
from typing import Optional

from .analysis import AnalysisContext, AnalysisResult


@dataclass(frozen=True)
class Verification:
    valid: bool
    optimal: Optional[bool]
    complete: bool
    checks: int
    reason: str


def verify_challenge(context: AnalysisContext, result: AnalysisResult,
                     *, verify_optimality: bool = True,
                     max_evaluations: Optional[int] = None) -> Verification:
    """Verify challenge output against original semantics and recorded scope.

    valid means the reported status/witness passes basic checks.
    optimal=True proves no smaller witness in the *declared* candidate set.
    optimal=None means it was not established (e.g. budget or opted out).
    For `stable`, complete=True establishes all additions were tested here.
    """
    if max_evaluations is not None and (type(max_evaluations) is not int or max_evaluations < 0):
        raise ValueError("max_evaluations must be a nonnegative integer or None")
    if result.method not in ("challenge", "z3_challenge", "leap") or result.target != context.target:
        return Verification(False, None, False, 0, "result targets a different query")
    base = context.evaluate()
    checks = 1
    if base != result.original_verdict:
        return Verification(False, None, False, checks, "base verdict mismatch")
    options = result.candidates
    available = set(context.graph.leaves(context.target)) - context.evidence.facts
    if tuple(sorted(set(options))) != options or not set(options).issubset(available):
        return Verification(False, None, False, checks, "invalid candidate universe")
    if result.status not in ("flipped", "stable", "budget_exceeded"):
        return Verification(False, None, False, checks, "unknown status")
    if not (0 <= result.searched_up_to <= len(options)):
        return Verification(False, None, False, checks, "invalid search depth")
    if result.status == "flipped":
        if (not result.witness or tuple(sorted(set(result.witness))) != result.witness
                or not set(result.witness).issubset(options) or result.radius != len(result.witness)
                or result.searched_up_to != result.radius):
            return Verification(False, None, False, checks, "malformed witness/radius")
        witness_verdict = context.evaluate(context.evidence.facts.union(result.witness))
        checks += 1
        if witness_verdict == base:
            return Verification(False, None, False, checks, "witness does not flip verdict")
        if not verify_optimality:
            return Verification(True, None, False, checks, "valid witness; minimality unchecked")
        for size in range(1, result.radius):
            for combo in combinations(options, size):
                if max_evaluations is not None and checks >= max_evaluations:
                    return Verification(True, None, False, checks, "minimality budget exhausted")
                checks += 1
                if context.evaluate(context.evidence.facts.union(combo)) != base:
                    return Verification(True, False, True, checks, "a smaller witness exists")
        return Verification(True, True, True, checks, "minimum-cardinality witness verified")
    if result.radius is not None or result.witness:
        return Verification(False, None, False, checks, "non-flipped result includes witness")
    if result.status == "stable" and result.searched_up_to != len(options):
        return Verification(False, None, False, checks, "stability cannot be claimed before exhaustion")
    if result.status == "budget_exceeded" and result.searched_up_to >= len(options):
        return Verification(False, None, False, checks, "wrong budget status")
    if not verify_optimality:
        return Verification(True, None, False, checks, "unverified no-flip report")
    for size in range(1, result.searched_up_to + 1):
        for combo in combinations(options, size):
            if max_evaluations is not None and checks >= max_evaluations:
                return Verification(True, None, False, checks, "verification budget exhausted")
            checks += 1
            if context.evaluate(context.evidence.facts.union(combo)) != base:
                return Verification(False, None, True, checks, "missed a flipping witness")
    if result.status == "stable":
        return Verification(True, None, True, checks, "stability exhaustively verified")
    return Verification(True, None, True, checks, "no flip within declared budget")
