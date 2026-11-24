"""PYTHEN v2 framework, semantics, registry, robustness, and artifacts."""
import json
import random
import tempfile
import unittest
from itertools import combinations
from pathlib import Path

from pythen import (RuleGraph, EvidenceState, Intervention, Reasoner,
                    Analyzer, AnalysisResult, RuleTreeEvaluator)
from pythen.research import export_experiment


CONTRACT = [
    {"p": "voidable", "op": "ALL", "conditions": ["minor"], "exceptions": ["necessity"]},
    {"p": "necessity", "op": "ALL", "conditions": ["essential", "fair_price"], "exceptions": []},
]


def brute(graph, facts, target, candidates):
    known = frozenset(facts)
    base = graph.evaluate(known, target)
    for n in range(1, len(candidates) + 1):
        for extra in combinations(sorted(candidates), n):
            if graph.evaluate(known | set(extra), target) != base:
                return n, extra
    return None, ()


class FrameworkTests(unittest.TestCase):
    def test_radius_witness_contract(self):
        r = Reasoner(CONTRACT, ["minor"])
        self.assertTrue(r.evaluate("voidable"))
        result = r.challenge("voidable")
        self.assertEqual(result.status, "flipped")
        self.assertEqual(result.radius, 2)
        self.assertEqual(result.flip_distance, 2)
        self.assertEqual(result.witness, ("essential", "fair_price"))
        self.assertFalse(result.counterfactual_verdict)
        v = r.verify(result)
        self.assertTrue(v.valid)
        self.assertTrue(v.optimal)
        self.assertTrue(v.complete)

    def test_intervention_is_immutable(self):
        r = Reasoner(CONTRACT, ["minor"])
        next_r = r.intervene(Intervention(add={"essential", "fair_price"}))
        self.assertTrue(r.evaluate("voidable"))
        self.assertFalse(next_r.evaluate("voidable"))
        self.assertEqual(r.facts, frozenset(["minor"]))
        self.assertEqual(next_r.facts, frozenset(["minor", "essential", "fair_price"]))
        self.assertIs(r.graph, next_r.graph)
        restored = next_r.intervene(Intervention(remove={"essential", "fair_price"}))
        self.assertTrue(restored.evaluate("voidable"))

    def test_rule_head_interventions_are_rejected(self):
        r = Reasoner(CONTRACT, ["minor"])
        with self.assertRaisesRegex(ValueError, "derived"):
            r.intervene(Intervention(add=["necessity"]))

    def test_bounded_is_not_stable(self):
        r = Reasoner(CONTRACT, ["minor"])
        result = r.challenge("voidable", max_changes=1)
        self.assertEqual(result.status, "budget_exceeded")
        self.assertEqual(result.guarantee, "bounded")
        self.assertIsNone(result.radius)
        self.assertTrue(r.verify(result).valid)
        self.assertIsNone(r.verify(result).optimal)

    def test_stable_exact(self):
        r = Reasoner([{"p": "p", "op": "ALL", "conditions": ["a"], "exceptions": []}], ["a"])
        result = r.challenge("p")
        self.assertEqual(result.status, "stable")
        self.assertEqual(result.evaluations, 1)
        self.assertTrue(r.verify(result).complete)

    def test_false_to_true(self):
        r = Reasoner(CONTRACT, [])
        result = r.challenge("voidable")
        self.assertFalse(result.original_verdict)
        self.assertEqual(result.radius, 1)
        self.assertEqual(result.witness, ("minor",))
        self.assertTrue(r.verify(result).optimal)

    def test_exception_first_empty_all(self):
        rules = [
            {"p": "always", "op": "AND", "conditions": [], "exceptions": []},
            {"p": "never", "op": "OR", "conditions": [], "exceptions": []},
            {"p": "blocked", "op": "AND", "conditions": [], "exceptions": ["x"]},
        ]
        r = Reasoner(rules)
        self.assertTrue(r.evaluate("always"))
        self.assertFalse(r.evaluate("never"))
        self.assertTrue(r.evaluate("blocked"))
        self.assertEqual(r.challenge("blocked").witness, ("x",))

    def test_shared_node_no_unsound_min_plus(self):
        rules = [
            {"p": "p", "op": "ALL", "conditions": ["x"], "exceptions": ["x"]},
        ]
        r = Reasoner(rules)
        self.assertEqual(r.challenge("p").status, "stable")
        self.assertTrue(r.verify(r.challenge("p")).complete)

    def test_target_leaf(self):
        r = Reasoner(CONTRACT, [])
        self.assertEqual(r.challenge("unlisted_leaf").radius, 1)
        self.assertEqual(r.challenge("unlisted_leaf").witness, ("unlisted_leaf",))
        self.assertEqual(r.with_facts(["unlisted_leaf"]).challenge("unlisted_leaf").status, "stable")

    def test_candidates_restrict_domain(self):
        r = Reasoner(CONTRACT, ["minor"])
        limited = r.challenge("voidable", candidates=["essential"])
        self.assertEqual(limited.status, "stable")
        with self.assertRaises(ValueError):
            r.challenge("voidable", candidates=["minor"])
        with self.assertRaises(ValueError):
            r.challenge("voidable", candidates=["voidable"])
        with self.assertRaises(ValueError):
            r.challenge("voidable", candidates="essential")
        with self.assertRaises(ValueError):
            r.challenge("voidable", max_changes=-1)
        with self.assertRaises(ValueError):
            r.challenge("voidable", max_changes=True)

    def test_cycle_and_duplicate(self):
        with self.assertRaisesRegex(ValueError, "Cyclic"):
            Reasoner([{"p": "a", "op": "ALL", "conditions": ["b"], "exceptions": []},
                      {"p": "b", "op": "ALL", "conditions": [], "exceptions": ["a"]}])
        with self.assertRaisesRegex(ValueError, "duplicate"):
            Reasoner(CONTRACT + [dict(CONTRACT[0])])

    def test_input_is_not_mutated(self):
        rules = [{"p": "p", "op": "ALL", "conditions": ["x"]}]
        r = Reasoner(rules)
        rules[0]["conditions"].append("y")
        self.assertTrue(r.with_facts(["x"]).evaluate("p"))
        self.assertNotIn("exceptions", rules[0])
        self.assertEqual(r.graph.to_rules()[0]["conditions"], ["x"])
        with self.assertRaises(TypeError):
            r.graph.nodes["p"] = "bad"

    def test_deterministic_hash(self):
        self.assertEqual(RuleGraph(CONTRACT).fingerprint, RuleGraph(reversed(CONTRACT)).fingerprint)

    def test_method_registry(self):
        class CountAnalyzer(Analyzer):
            name = "count"
            def analyze(self, context, **params):
                return AnalysisResult(self.name, context.target, context.evaluate(),
                                      "complete", metadata={"leaves": len(context.graph.leaves())})
        r = Reasoner(CONTRACT, ["minor"])
        r.register(CountAnalyzer())
        self.assertEqual(r.analyze("voidable", method="count").metadata["leaves"], 3)
        with self.assertRaises(ValueError):
            r.register(CountAnalyzer())
        self.assertEqual(r.intervene(Intervention(add=["essential"])).analyze("voidable", method="count").status, "complete")
        self.assertEqual(r.analyze("voidable", method="leap").radius, 2)

    def test_verification_catches_fake_witness(self):
        r = Reasoner(CONTRACT, ["minor"])
        fake = AnalysisResult("challenge", "voidable", True, "flipped", 1,
                              ("essential",), ("essential", "fair_price"), 2, 1)
        check = r.verify(fake)
        self.assertFalse(check.valid)
        self.assertFalse(check.complete)

    def test_verification_catches_nonminimum_witness(self):
        r = Reasoner([{"p": "p", "op": "ANY", "conditions": ["a", "b"], "exceptions": []}])
        fake = AnalysisResult("challenge", "p", False, "flipped", 2,
                              ("a", "b"), ("a", "b"), 4, 2)
        check = r.verify(fake)
        self.assertTrue(check.valid)
        self.assertFalse(check.optimal)

    def test_verification_budget_does_not_certify_optimal(self):
        r = Reasoner(CONTRACT, ["minor"])
        result = r.challenge("voidable")
        check = r.verify(result, max_evaluations=2)
        self.assertTrue(check.valid)
        self.assertIsNone(check.optimal)
        self.assertFalse(check.complete)

    def test_deterministic_json_export(self):
        r = Reasoner(CONTRACT, ["minor"])
        result = r.challenge("voidable")
        with tempfile.TemporaryDirectory() as td:
            export_experiment(Path(td) / "r.json", r.graph, r.evidence, result)
            data = json.loads((Path(td) / "r.json").read_text())
            self.assertEqual(data["analysis"]["radius"], 2)
            self.assertEqual(data["graph_sha256"], r.graph.fingerprint)

    def test_v1_equivalence_handcrafted(self):
        for facts in ([], ["minor"], ["essential"], ["minor", "essential"],
                      ["minor", "essential", "fair_price"]):
            v1 = RuleTreeEvaluator(CONTRACT)
            v2 = Reasoner(CONTRACT, facts)
            self.assertEqual(v1.evaluate(facts, "voidable"), v2.evaluate("voidable"))

    def test_random_small_graphs_against_v1_and_bruteforce(self):
        rng = random.Random(2026)
        for trial in range(120):
            rules = []
            available = ["f0", "f1", "f2", "f3", "f4"]
            for i in range(rng.randint(1, 5)):
                name = "p" + str(i)
                size = rng.randint(0, 4)
                conditions = [rng.choice(available) for _ in range(size)]
                exceptions = [rng.choice(available) for _ in range(rng.randint(0, 2))]
                rules.append({"p": name, "op": rng.choice(["ALL", "ANY"]),
                              "conditions": conditions, "exceptions": exceptions})
                available.append(name)
            target = rules[-1]["p"]
            facts = ["f" + str(i) for i in range(5) if rng.choice([False, True])]
            graph = RuleGraph(rules)
            r = Reasoner(graph, facts)
            v1 = RuleTreeEvaluator(rules)
            self.assertEqual(v1.evaluate(facts, target), r.evaluate(target), trial)
            cand = sorted(set(graph.leaves(target)) - set(facts))
            expected_r, _ = brute(graph, facts, target, cand)
            result = r.challenge(target)
            self.assertEqual(result.radius, expected_r, trial)
            check = r.verify(result)
            self.assertTrue(check.valid, trial)
            self.assertTrue(check.complete, trial)
            if expected_r is not None:
                self.assertTrue(check.optimal, trial)


if __name__ == "__main__":
    unittest.main()
