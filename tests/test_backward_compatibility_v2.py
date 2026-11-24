"""Regression tests ensuring PYTHEN v2 preserves public PYTHEN v1 APIs."""
import io
import unittest
from contextlib import redirect_stdout

import pythen
from pythen import (
    RuleTreeEvaluator, RuleValidationError, print_rule, print_rules,
    load_rules_from_json, save_rules_to_json,
)


class LegacyCompatibilityTests(unittest.TestCase):
    @staticmethod
    def rules():
        return [
            {"p": "eligible", "op": "ALL", "conditions": ["is_citizen", "adult"],
             "exceptions": ["disqualified"]},
            {"p": "adult", "op": "ALL", "conditions": ["over_18"], "exceptions": []},
        ]

    def test_public_version_and_metadata(self):
        self.assertEqual(pythen.__version__, '0.2.0a3')
        self.assertEqual(pythen.__license__, 'MIT')
        self.assertTrue(pythen.__author__)

    def test_json_helpers_are_importable_from_package(self):
        rules = self.rules()
        self.assertEqual(load_rules_from_json(save_rules_to_json(rules)), rules)

    def test_legacy_print_helpers(self):
        out = io.StringIO()
        with redirect_stdout(out):
            print_rule(self.rules()[0])
            print_rules(self.rules())
        self.assertIn('eligible', out.getvalue())

    def test_original_exception_and_trace_semantics(self):
        e = RuleTreeEvaluator(self.rules(), enable_trace=True)
        self.assertTrue(e.evaluate(['is_citizen', 'over_18'], 'eligible'))
        self.assertFalse(e.evaluate(['is_citizen', 'over_18', 'disqualified'], 'eligible'))
        self.assertTrue(any(item[1] == 'EXCEPTION_MET' for item in e.get_trace()))

    def test_closed_world_missing_citizenship(self):
        e = RuleTreeEvaluator(self.rules())
        self.assertFalse(e.evaluate(['over_18'], 'eligible'))

    def test_legacy_challenge_convenience_method(self):
        e = RuleTreeEvaluator(self.rules())
        r = e.challenge(['is_citizen', 'over_18'], 'eligible')
        self.assertEqual((r.status, r.radius), ('flipped', 1))
        self.assertEqual(r.witness, ('disqualified',))

    def test_validation_error_type_preserved(self):
        with self.assertRaises(RuleValidationError):
            RuleTreeEvaluator([{'p': 'x', 'conditions': []}])


if __name__ == '__main__':
    unittest.main()
