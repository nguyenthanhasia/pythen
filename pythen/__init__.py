"""PYTHEN 2: extensible and verifiable defeasible reasoning.

The original RuleTreeEvaluator and utility functions remain available.
"""
__version__ = "0.2.0a3"
__author__ = "PYTHEN Contributors"
__license__ = "MIT"
from .evaluator import RuleTreeEvaluator
from .utils import (
    validate_rule, validate_rules, log_message, RuleValidationError,
    load_rules_from_json, save_rules_to_json, print_rule, print_rules,
)

__all__ = [
    "RuleTreeEvaluator",
    "validate_rule",
    "validate_rules",
    "log_message",
    "RuleValidationError",
    "load_rules_from_json",
    "save_rules_to_json",
    "print_rule",
    "print_rules",
    "RuleGraph",
    "RuleNode",
    "EvidenceState",
    "Intervention",
    "Analyzer",
    "AnalysisContext",
    "AnalysisResult",
    "ChallengeAnalyzer",
    "Verification",
    "verify_challenge",
    "Reasoner",
    "ChallengeResult",
    "Z3ChallengeAnalyzer",
    "LeapAnalyzer",
]


# PYTHEN v2 additive research framework
from .graph import RuleGraph, RuleNode
from .intervention import EvidenceState, Intervention
from .analysis import Analyzer, AnalysisContext, AnalysisResult
from .challenge import ChallengeAnalyzer
from .verification import Verification, verify_challenge
from .reasoner import Reasoner
from .challenge import ChallengeResult

from .solvers import Z3ChallengeAnalyzer

from .leap import LeapAnalyzer
