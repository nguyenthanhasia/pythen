"""
PYTHEN: A Flexible Framework for Legal Reasoning in Python

PYTHEN is a Python-based framework for defeasible legal reasoning that combines
the power of logic programming with the accessibility and flexibility of Python.

Key Features:
- Simple JSON-based rule syntax
- Support for both conjunctive (ALL) and disjunctive (ANY) conditions
- Explicit exception handling for defeasible reasoning
- Easy integration with LLMs for autoformalization
- Comprehensive documentation and examples

Example:
    >>> from pythen import RuleTreeEvaluator
    >>> rules = [
    ...     {
    ...         "p": "erasure_applicable",
    ...         "op": "ANY",
    ...         "conditions": ["no_longer_necessary", "consent_withdrawn"],
    ...         "exceptions": ["legal_obligation"]
    ...     }
    ... ]
    >>> evaluator = RuleTreeEvaluator(rules)
    >>> facts = ["consent_withdrawn"]
    >>> result = evaluator.evaluate(facts, "erasure_applicable")
    >>> print(result)  # True
"""

__version__ = "0.1.0"
__author__ = "PYTHEN Contributors"
__license__ = "MIT"

from .evaluator import RuleTreeEvaluator
from .utils import validate_rule, validate_rules, log_message, RuleValidationError

__all__ = [
    "RuleTreeEvaluator",
    "validate_rule",
    "validate_rules",
    "log_message",
    "RuleValidationError",
]
