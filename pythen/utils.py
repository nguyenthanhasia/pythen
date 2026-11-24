"""Minimal unmodified PYTHEN v1 validation and logging behavior for tests."""
import logging
logger = logging.getLogger(__name__)


class RuleValidationError(Exception):
    pass


def log_message(level, message):
    logger.log(getattr(logging, level.upper(), logging.INFO), message)


def validate_rule(rule):
    if not isinstance(rule, dict):
        raise RuleValidationError('Rule must be a dictionary')
    if not isinstance(rule.get('p'), str):
        raise RuleValidationError("Rule must have 'p' (proposition) field")
    if rule.get('op') not in ('ALL', 'ANY', 'AND', 'OR'):
        raise RuleValidationError("Rule invalid 'op'")
    if not isinstance(rule.get('conditions'), list):
        raise RuleValidationError("Rule requires conditions list")
    if not all(isinstance(x, str) for x in rule['conditions']):
        raise RuleValidationError('Invalid condition')
    rule.setdefault('exceptions', [])
    if not isinstance(rule['exceptions'], list) or not all(isinstance(x, str) for x in rule['exceptions']):
        raise RuleValidationError('Invalid exceptions')
    return True


def validate_rules(rules):
    if not isinstance(rules, list) or not rules:
        raise RuleValidationError('Rules must be a nonempty list')
    for item in rules:
        validate_rule(item)
    heads = [x['p'] for x in rules]
    if len(set(heads)) != len(heads):
        raise RuleValidationError('Duplicate propositions')
    return True
