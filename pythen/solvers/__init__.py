"""Optional exact solver adapters. No native backend is required by the base package."""
from .z3_native import Z3ChallengeAnalyzer
__all__ = ["Z3ChallengeAnalyzer"]
