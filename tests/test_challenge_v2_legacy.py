"""Regression tests for exact addition-only robustness."""
import itertools
import unittest

from pythen import RuleTreeEvaluator


def rule(p, conditions, exceptions=(), op="ALL"):
    return {"p": p, "op": op, "conditions": list(conditions), "exceptions": list(exceptions)}


class ChallengeTests(unittest.TestCase):
    def test_one_fact_exception(self):
        engine = RuleTreeEvaluator([rule("voidable", ["minor"], ["necessities"])])
        result = engine.challenge(["minor"], "voidable")
        self.assertEqual((result.original_verdict, result.counterfactual_verdict), (True, False))
        self.assertEqual((result.status, result.radius, result.witness), ("flipped", 1, ("necessities",)))

    def test_minimal_pair_for_conjunctive_exception(self):
        engine = RuleTreeEvaluator([
            rule("voidable", ["minor"], ["necessities"]),
            rule("necessities", ["essential", "fair_price"]),
        ])
        result = engine.challenge(["minor"], "voidable")
        self.assertEqual(result.radius, 2)
        self.assertEqual(result.witness, ("essential", "fair_price"))
        self.assertEqual(result.evaluations, 4)

    def test_false_to_true(self):
        engine = RuleTreeEvaluator([rule("eligible", ["adult", "citizen"])])
        result = engine.challenge(["adult"], "eligible")
        self.assertFalse(result.original_verdict)
        self.assertEqual(result.witness, ("citizen",))
        self.assertTrue(result.counterfactual_verdict)

    def test_multiple_routes_and_shared_nodes(self):
        rules = [
            rule("legal", ["a", "b"], ["barred"]),
            rule("a", ["x"], op="ANY"),
            rule("b", ["x", "y"], op="ANY"),
            rule("barred", ["p", "q"]),
        ]
        engine = RuleTreeEvaluator(rules)
        self.assertEqual(engine.challenge([], "legal").witness, ("x",))
        self.assertEqual(engine.challenge(["x"], "legal").witness, ("p", "q"))

    def test_nested_nonmonotonic_exception(self):
        # r is true when x, except if y; adding x can *disable* r via z.
        engine = RuleTreeEvaluator([
            rule("root", ["r"]),
            rule("r", ["x"], ["y"]),
            rule("y", ["z"]),
        ])
        self.assertEqual(engine.challenge(["x"], "root").witness, ("z",))
        self.assertEqual(engine.challenge(["x", "z"], "root").status, "stable")

    def test_stable_when_no_candidates(self):
        engine = RuleTreeEvaluator([rule("always", [])])
        result = engine.challenge([], "always")
        self.assertEqual((result.status, result.radius, result.witness), ("stable", None, ()))
        self.assertEqual(result.evaluations, 1)

    def test_stable_even_when_candidates_exist(self):
        engine = RuleTreeEvaluator([rule("contradiction", ["x"], ["x"])])
        result = engine.challenge([], "contradiction")
        self.assertEqual(result.status, "stable")
        self.assertEqual(result.candidates, ("x",))

    def test_budget_exceeded_is_not_stable(self):
        engine = RuleTreeEvaluator([rule("p", ["x", "y", "z"])])
        result = engine.challenge([], "p", max_changes=2)
        self.assertEqual(result.status, "budget_exceeded")
        self.assertIsNone(result.radius)
        self.assertEqual(result.searched_up_to, 2)
        self.assertEqual(engine.challenge([], "p", max_changes=3).radius, 3)

    def test_candidate_restrictions(self):
        engine = RuleTreeEvaluator([rule("p", ["x", "y"], op="ANY")])
        result = engine.challenge([], "p", candidates=["y"])
        self.assertEqual(result.witness, ("y",))
        self.assertEqual(result.candidates, ("y",))
        self.assertEqual(engine.challenge([], "p", candidates=[]).status, "stable")

    def test_only_reachable_leaf_candidates(self):
        engine = RuleTreeEvaluator([rule("p", ["x"]), rule("unrelated", ["y"])])
        self.assertEqual(engine.challenge([], "p").candidates, ("x",))

    def test_reject_non_leaf_unknown_or_existing_candidate(self):
        engine = RuleTreeEvaluator([rule("p", ["x"]), rule("q", ["y"])])
        for c in (["p"], ["y"], ["x", "bad"], ["x", 1], "x", ["x"]):
            with self.subTest(c=c):
                if c == ["x"]:
                    with self.assertRaises(ValueError):
                        engine.challenge(["x"], "p", candidates=c)
                else:
                    with self.assertRaises(ValueError):
                        engine.challenge([], "p", candidates=c)

    def test_cycle_rejected(self):
        engine = RuleTreeEvaluator([rule("p", ["q"]), rule("q", ["p"])])
        with self.assertRaisesRegex(ValueError, "Cyclic"):
            engine.challenge([], "p")

    def test_preserves_facts_and_evaluation_trace(self):
        engine = RuleTreeEvaluator([rule("p", ["x"], ["y"])], enable_trace=True)
        facts = ["x"]
        engine.evaluate(facts, "p")
        trace = engine.get_trace()
        original_entries = tuple(trace)
        engine.challenge(facts, "p")
        self.assertEqual(facts, ["x"])
        self.assertIs(engine.get_trace(), trace)
        self.assertEqual(tuple(engine.get_trace()), original_entries)
        self.assertTrue(engine.enable_trace)

    def test_no_rule_target_is_leaf(self):
        engine = RuleTreeEvaluator([rule("other", ["x"])])
        self.assertEqual(engine.challenge([], "unknown").witness, ("unknown",))

    def test_invalid_parameters(self):
        engine = RuleTreeEvaluator([rule("p", ["x"])])
        for kw in ({"max_changes": -1}, {"max_changes": 1.2}, {"max_changes": True}):
            with self.assertRaises(ValueError):
                engine.challenge([], "p", **kw)
        with self.assertRaises(ValueError):
            engine.challenge("x", "p")
        with self.assertRaises(ValueError):
            engine.challenge([], "")

    def test_bruteforce_crosscheck_random_dags(self):
        import random
        rng = random.Random(2026)
        leaves = ["a", "b", "c", "d"]
        for case in range(100):
            rules = []
            for i in range(4):
                earlier = leaves + ["r{}".format(j) for j in range(i)]
                rules.append(rule("r{}".format(i), rng.sample(earlier, rng.randrange(0, min(4, len(earlier)) + 1)), rng.sample(earlier, rng.randrange(0, 3)), rng.choice(["ALL", "ANY"])))
            engine = RuleTreeEvaluator(rules)
            facts = [f for f in leaves if rng.randrange(2)]
            result = engine.challenge(facts, "r3")
            baseline = engine.evaluate(facts, "r3")
            available = [f for f in leaves if f not in facts]
            expected = None
            for count in range(len(available) + 1):
                if any(engine.evaluate(facts + list(c), "r3") != baseline for c in itertools.combinations(available, count)):
                    expected = count
                    break
            self.assertEqual(result.radius, expected, msg=str(case))
            if result.status == "flipped":
                self.assertNotEqual(engine.evaluate(facts + list(result.witness), "r3"), baseline)
            else:
                self.assertEqual(result.status, "stable")

if __name__ == '__main__':
    unittest.main()
