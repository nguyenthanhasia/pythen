"""
Unit tests for utility functions.
"""

import unittest
import json
from pythen.utils import (
    validate_rule,
    validate_rules,
    load_rules_from_json,
    save_rules_to_json,
    RuleValidationError
)


class TestRuleValidation(unittest.TestCase):
    """Test cases for rule validation functions."""
    
    def test_valid_rule(self):
        """Test validation of a valid rule."""
        rule = {
            "p": "test_prop",
            "op": "ALL",
            "conditions": ["cond1", "cond2"],
            "exceptions": []
        }
        self.assertTrue(validate_rule(rule))
    
    def test_missing_p_field(self):
        """Test that missing 'p' field raises error."""
        rule = {
            "op": "ALL",
            "conditions": [],
            "exceptions": []
        }
        with self.assertRaises(RuleValidationError):
            validate_rule(rule)
    
    def test_missing_op_field(self):
        """Test that missing 'op' field raises error."""
        rule = {
            "p": "test",
            "conditions": [],
            "exceptions": []
        }
        with self.assertRaises(RuleValidationError):
            validate_rule(rule)
    
    def test_invalid_op_value(self):
        """Test that invalid 'op' value raises error."""
        rule = {
            "p": "test",
            "op": "INVALID",
            "conditions": [],
            "exceptions": []
        }
        with self.assertRaises(RuleValidationError):
            validate_rule(rule)
    
    def test_valid_op_values(self):
        """Test that all valid 'op' values are accepted."""
        for op in ["ALL", "ANY", "AND", "OR"]:
            rule = {
                "p": "test",
                "op": op,
                "conditions": [],
                "exceptions": []
            }
            self.assertTrue(validate_rule(rule))
    
    def test_missing_conditions_field(self):
        """Test that missing 'conditions' field raises error."""
        rule = {
            "p": "test",
            "op": "ALL",
            "exceptions": []
        }
        with self.assertRaises(RuleValidationError):
            validate_rule(rule)
    
    def test_conditions_not_list(self):
        """Test that non-list 'conditions' raises error."""
        rule = {
            "p": "test",
            "op": "ALL",
            "conditions": "not_a_list",
            "exceptions": []
        }
        with self.assertRaises(RuleValidationError):
            validate_rule(rule)
    
    def test_non_string_condition(self):
        """Test that non-string condition raises error."""
        rule = {
            "p": "test",
            "op": "ALL",
            "conditions": ["valid_string", 123],
            "exceptions": []
        }
        with self.assertRaises(RuleValidationError):
            validate_rule(rule)
    
    def test_exceptions_not_list(self):
        """Test that non-list 'exceptions' raises error."""
        rule = {
            "p": "test",
            "op": "ALL",
            "conditions": [],
            "exceptions": "not_a_list"
        }
        with self.assertRaises(RuleValidationError):
            validate_rule(rule)
    
    def test_empty_exceptions_allowed(self):
        """Test that empty exceptions list is allowed."""
        rule = {
            "p": "test",
            "op": "ALL",
            "conditions": ["cond"],
            "exceptions": []
        }
        self.assertTrue(validate_rule(rule))
    
    def test_missing_exceptions_field_allowed(self):
        """Test that missing 'exceptions' field is allowed."""
        rule = {
            "p": "test",
            "op": "ALL",
            "conditions": ["cond"]
        }
        self.assertTrue(validate_rule(rule))
        # Check that exceptions field was added
        self.assertIn("exceptions", rule)
        self.assertEqual(rule["exceptions"], [])


class TestRulesValidation(unittest.TestCase):
    """Test cases for validating rule sets."""
    
    def test_valid_rule_set(self):
        """Test validation of a valid rule set."""
        rules = [
            {
                "p": "rule1",
                "op": "ALL",
                "conditions": ["cond1"],
                "exceptions": []
            },
            {
                "p": "rule2",
                "op": "ANY",
                "conditions": ["cond2"],
                "exceptions": []
            }
        ]
        self.assertTrue(validate_rules(rules))
    
    def test_empty_rule_set(self):
        """Test that empty rule set raises error."""
        with self.assertRaises(RuleValidationError):
            validate_rules([])
    
    def test_duplicate_propositions(self):
        """Test that duplicate propositions raise error."""
        rules = [
            {
                "p": "duplicate",
                "op": "ALL",
                "conditions": [],
                "exceptions": []
            },
            {
                "p": "duplicate",
                "op": "ANY",
                "conditions": [],
                "exceptions": []
            }
        ]
        with self.assertRaises(RuleValidationError):
            validate_rules(rules)
    
    def test_invalid_rule_in_set(self):
        """Test that invalid rule in set raises error."""
        rules = [
            {
                "p": "valid",
                "op": "ALL",
                "conditions": [],
                "exceptions": []
            },
            {
                "p": "invalid",
                # Missing 'op'
                "conditions": [],
                "exceptions": []
            }
        ]
        with self.assertRaises(RuleValidationError):
            validate_rules(rules)


class TestJSONHandling(unittest.TestCase):
    """Test cases for JSON loading and saving."""
    
    def test_save_rules_to_json(self):
        """Test saving rules to JSON."""
        rules = [
            {
                "p": "test",
                "op": "ALL",
                "conditions": ["cond"],
                "exceptions": []
            }
        ]
        json_str = save_rules_to_json(rules)
        self.assertIsInstance(json_str, str)
        parsed = json.loads(json_str)
        self.assertEqual(len(parsed), 1)
        self.assertEqual(parsed[0]["p"], "test")
    
    def test_load_rules_from_json(self):
        """Test loading rules from JSON."""
        json_str = '''[
            {
                "p": "test",
                "op": "ALL",
                "conditions": ["cond"],
                "exceptions": []
            }
        ]'''
        rules = load_rules_from_json(json_str)
        self.assertEqual(len(rules), 1)
        self.assertEqual(rules[0]["p"], "test")
    
    def test_load_invalid_json(self):
        """Test that invalid JSON raises error."""
        invalid_json = "{ invalid json }"
        with self.assertRaises(ValueError):
            load_rules_from_json(invalid_json)
    
    def test_roundtrip_json(self):
        """Test that rules survive a save-load roundtrip."""
        original_rules = [
            {
                "p": "rule1",
                "op": "ALL",
                "conditions": ["cond1", "cond2"],
                "exceptions": ["exc1"]
            }
        ]
        json_str = save_rules_to_json(original_rules)
        loaded_rules = load_rules_from_json(json_str)
        self.assertEqual(original_rules, loaded_rules)


if __name__ == "__main__":
    unittest.main()
