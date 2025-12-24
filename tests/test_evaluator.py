"""
Unit tests for the RuleTreeEvaluator class.
"""

import unittest
from pythen import RuleTreeEvaluator, RuleValidationError


class TestRuleTreeEvaluator(unittest.TestCase):
    """Test cases for RuleTreeEvaluator."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.simple_rules = [
            {
                "p": "can_vote",
                "op": "ALL",
                "conditions": ["is_citizen", "is_over_18"],
                "exceptions": []
            }
        ]
        
        self.rules_with_exceptions = [
            {
                "p": "contract_voidable",
                "op": "ANY",
                "conditions": ["party_is_minor"],
                "exceptions": ["contract_for_necessities"]
            }
        ]
        
        self.nested_rules = [
            {
                "p": "can_vote",
                "op": "ALL",
                "conditions": ["is_citizen", "is_over_18"],
                "exceptions": ["is_disqualified"]
            },
            {
                "p": "is_over_18",
                "op": "ALL",
                "conditions": ["age_is_18_or_more"],
                "exceptions": []
            },
            {
                "p": "is_disqualified",
                "op": "ANY",
                "conditions": ["has_felony", "is_mentally_incompetent"],
                "exceptions": []
            }
        ]
    
    def test_initialization(self):
        """Test evaluator initialization."""
        evaluator = RuleTreeEvaluator(self.simple_rules)
        self.assertEqual(len(evaluator.node_map), 1)
        self.assertIn("can_vote", evaluator.node_map)
    
    def test_simple_all_conditions_met(self):
        """Test ALL operator when all conditions are met."""
        evaluator = RuleTreeEvaluator(self.simple_rules)
        facts = ["is_citizen", "is_over_18"]
        result = evaluator.evaluate(facts, "can_vote")
        self.assertTrue(result)
    
    def test_simple_all_conditions_not_met(self):
        """Test ALL operator when not all conditions are met."""
        evaluator = RuleTreeEvaluator(self.simple_rules)
        facts = ["is_citizen"]  # Missing is_over_18
        result = evaluator.evaluate(facts, "can_vote")
        self.assertFalse(result)
    
    def test_any_operator_one_condition_met(self):
        """Test ANY operator when one condition is met."""
        rules = [
            {
                "p": "eligible",
                "op": "ANY",
                "conditions": ["has_degree", "has_experience"],
                "exceptions": []
            }
        ]
        evaluator = RuleTreeEvaluator(rules)
        facts = ["has_experience"]
        result = evaluator.evaluate(facts, "eligible")
        self.assertTrue(result)
    
    def test_any_operator_no_conditions_met(self):
        """Test ANY operator when no conditions are met."""
        rules = [
            {
                "p": "eligible",
                "op": "ANY",
                "conditions": ["has_degree", "has_experience"],
                "exceptions": []
            }
        ]
        evaluator = RuleTreeEvaluator(rules)
        facts = []
        result = evaluator.evaluate(facts, "eligible")
        self.assertFalse(result)
    
    def test_exception_defeats_rule(self):
        """Test that an exception defeats a rule."""
        evaluator = RuleTreeEvaluator(self.rules_with_exceptions)
        facts = ["party_is_minor", "contract_for_necessities"]
        result = evaluator.evaluate(facts, "contract_voidable")
        self.assertFalse(result)
    
    def test_exception_does_not_defeat_rule(self):
        """Test that when exception is not met, rule is not defeated."""
        evaluator = RuleTreeEvaluator(self.rules_with_exceptions)
        facts = ["party_is_minor"]
        result = evaluator.evaluate(facts, "contract_voidable")
        self.assertTrue(result)
    
    def test_nested_rules(self):
        """Test evaluation with nested rules."""
        evaluator = RuleTreeEvaluator(self.nested_rules)
        
        # Case 1: Person can vote
        facts_1 = ["age_is_18_or_more"]
        result_1 = evaluator.evaluate(facts_1, "can_vote")
        self.assertTrue(result_1)
        
        # Case 2: Person cannot vote due to felony
        facts_2 = ["age_is_18_or_more", "has_felony"]
        result_2 = evaluator.evaluate(facts_2, "can_vote")
        self.assertFalse(result_2)
    
    def test_fact_not_in_rule_set(self):
        """Test evaluation of a fact not defined in the rule set."""
        evaluator = RuleTreeEvaluator(self.simple_rules)
        facts = ["is_citizen", "is_over_18"]
        result = evaluator.evaluate(facts, "is_citizen")
        self.assertTrue(result)
    
    def test_get_applicable_rules(self):
        """Test retrieving applicable rules."""
        evaluator = RuleTreeEvaluator(self.simple_rules)
        rule = evaluator.get_applicable_rules("can_vote")
        self.assertIsNotNone(rule)
        self.assertEqual(rule["p"], "can_vote")
    
    def test_get_applicable_rules_not_found(self):
        """Test retrieving a rule that doesn't exist."""
        evaluator = RuleTreeEvaluator(self.simple_rules)
        rule = evaluator.get_applicable_rules("nonexistent")
        self.assertIsNone(rule)
    
    def test_get_all_predicates(self):
        """Test retrieving all predicates."""
        evaluator = RuleTreeEvaluator(self.nested_rules)
        predicates = evaluator.get_all_predicates()
        self.assertEqual(len(predicates), 3)
        self.assertIn("can_vote", predicates)
        self.assertIn("is_over_18", predicates)
        self.assertIn("is_disqualified", predicates)
    
    def test_explain_method(self):
        """Test the explain method."""
        evaluator = RuleTreeEvaluator(self.simple_rules)
        facts = ["is_citizen", "is_over_18"]
        explanation = evaluator.explain(facts, "can_vote")
        self.assertIn("can_vote", explanation)
        self.assertIn("True", explanation)
    
    def test_trace_enabled(self):
        """Test that tracing works when enabled."""
        evaluator = RuleTreeEvaluator(self.simple_rules, enable_trace=True)
        facts = ["is_citizen", "is_over_18"]
        evaluator.evaluate(facts, "can_vote")
        trace = evaluator.get_trace()
        self.assertGreater(len(trace), 0)
    
    def test_trace_disabled(self):
        """Test that tracing is empty when disabled."""
        evaluator = RuleTreeEvaluator(self.simple_rules, enable_trace=False)
        facts = ["is_citizen", "is_over_18"]
        evaluator.evaluate(facts, "can_vote")
        trace = evaluator.get_trace()
        self.assertEqual(len(trace), 0)
    
    def test_invalid_rule_set(self):
        """Test that invalid rule sets raise an error."""
        invalid_rules = [
            {
                "p": "test",
                # Missing 'op' field
                "conditions": [],
                "exceptions": []
            }
        ]
        with self.assertRaises(RuleValidationError):
            RuleTreeEvaluator(invalid_rules)


if __name__ == "__main__":
    unittest.main()
