"""
Utility functions for PYTHEN framework.

Includes logging, validation, and helper functions.
"""

import logging
from typing import List, Dict, Any
from datetime import datetime


class RuleValidationError(Exception):
    """Exception raised when a rule validation fails."""
    pass


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def log_message(level: str, message: str) -> None:
    """
    Log a message with the specified level.
    
    Args:
        level: Log level ('DEBUG', 'INFO', 'WARNING', 'ERROR')
        message: Message to log
    """
    level_map = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR,
    }
    
    log_level = level_map.get(level.upper(), logging.INFO)
    logger.log(log_level, message)


def validate_rule(rule: Dict[str, Any]) -> bool:
    """
    Validate a single rule dictionary.
    
    A valid rule must have:
    - 'p': proposition name (string)
    - 'op': operator ('ALL', 'ANY', 'AND', 'OR')
    - 'conditions': list of strings
    - 'exceptions': list of strings (can be empty)
    
    Args:
        rule: Rule dictionary to validate
        
    Returns:
        bool: True if valid
        
    Raises:
        RuleValidationError: If rule is invalid
    """
    if not isinstance(rule, dict):
        raise RuleValidationError("Rule must be a dictionary")
    
    # Check required fields
    if 'p' not in rule:
        raise RuleValidationError("Rule must have 'p' (proposition) field")
    
    if not isinstance(rule['p'], str):
        raise RuleValidationError("Proposition 'p' must be a string")
    
    if 'op' not in rule:
        raise RuleValidationError(f"Rule '{rule['p']}' must have 'op' (operator) field")
    
    op = rule['op']
    if op not in ['ALL', 'ANY', 'AND', 'OR']:
        raise RuleValidationError(
            f"Rule '{rule['p']}' has invalid operator '{op}'. "
            "Must be one of: 'ALL', 'ANY', 'AND', 'OR'"
        )
    
    if 'conditions' not in rule:
        raise RuleValidationError(f"Rule '{rule['p']}' must have 'conditions' field")
    
    conditions = rule['conditions']
    if not isinstance(conditions, list):
        raise RuleValidationError(
            f"Rule '{rule['p']}' conditions must be a list"
        )
    
    for i, cond in enumerate(conditions):
        if not isinstance(cond, str):
            raise RuleValidationError(
                f"Rule '{rule['p']}' condition {i} must be a string, got {type(cond)}"
            )
    
    # Check exceptions field (optional but should be a list if present)
    if 'exceptions' in rule:
        exceptions = rule['exceptions']
        if not isinstance(exceptions, list):
            raise RuleValidationError(
                f"Rule '{rule['p']}' exceptions must be a list"
            )
        
        for i, exc in enumerate(exceptions):
            if not isinstance(exc, str):
                raise RuleValidationError(
                    f"Rule '{rule['p']}' exception {i} must be a string, got {type(exc)}"
                )
    else:
        # Add empty exceptions list if not present
        rule['exceptions'] = []
    
    return True


def validate_rules(rules: List[Dict[str, Any]]) -> bool:
    """
    Validate a list of rules.
    
    Args:
        rules: List of rule dictionaries
        
    Returns:
        bool: True if all rules are valid
        
    Raises:
        RuleValidationError: If any rule is invalid
    """
    if not isinstance(rules, list):
        raise RuleValidationError("Rules must be a list")
    
    if len(rules) == 0:
        raise RuleValidationError("Rules list cannot be empty")
    
    for i, rule in enumerate(rules):
        try:
            validate_rule(rule)
        except RuleValidationError as e:
            raise RuleValidationError(f"Rule {i}: {str(e)}")
    
    # Check for duplicate propositions
    propositions = [rule['p'] for rule in rules]
    duplicates = [p for p in propositions if propositions.count(p) > 1]
    if duplicates:
        raise RuleValidationError(
            f"Duplicate propositions found: {set(duplicates)}"
        )
    
    return True


def load_rules_from_json(json_data: str) -> List[Dict[str, Any]]:
    """
    Load rules from JSON string.
    
    Args:
        json_data: JSON string containing rules
        
    Returns:
        List of rule dictionaries
        
    Raises:
        ValueError: If JSON is invalid
        RuleValidationError: If rules are invalid
    """
    import json
    
    try:
        rules = json.loads(json_data)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON: {str(e)}")
    
    validate_rules(rules)
    return rules


def save_rules_to_json(rules: List[Dict[str, Any]]) -> str:
    """
    Save rules to JSON string.
    
    Args:
        rules: List of rule dictionaries
        
    Returns:
        JSON string representation
    """
    import json
    
    validate_rules(rules)
    return json.dumps(rules, indent=2)


def print_rule(rule: Dict[str, Any]) -> None:
    """
    Pretty print a rule.
    
    Args:
        rule: Rule dictionary to print
    """
    print(f"\nRule: {rule['p']}")
    print(f"  Operator: {rule['op']}")
    print(f"  Conditions: {', '.join(rule.get('conditions', []))}")
    print(f"  Exceptions: {', '.join(rule.get('exceptions', []))}")


def print_rules(rules: List[Dict[str, Any]]) -> None:
    """
    Pretty print all rules.
    
    Args:
        rules: List of rule dictionaries
    """
    print(f"\n{'='*60}")
    print(f"Rule Set ({len(rules)} rules)")
    print(f"{'='*60}")
    
    for rule in rules:
        print_rule(rule)
    
    print(f"\n{'='*60}\n")
