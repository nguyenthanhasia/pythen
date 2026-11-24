"""Independent differential and regression checks for verified structural leaps."""
import random
import unittest

from pythen import LeapAnalyzer, Reasoner
from pythen.solvers.z3_native import Z3Experiment


def rule(name, op='ALL', conditions=(), exceptions=()):
    return {'p': name, 'op': op, 'conditions': list(conditions),
            'exceptions': list(exceptions)}


class LeapTests(unittest.TestCase):
    def compare(self, rules, facts, target, candidates=None, max_changes=None):
        r = Reasoner(rules, facts)
        python = r.challenge(target, candidates=candidates, max_changes=max_changes)
        leap = r.analyze(target, method='leap', candidates=candidates,
                         max_changes=max_changes)
        self.assertEqual(
            (leap.status, leap.radius, leap.original_verdict, leap.candidates,
             leap.searched_up_to, leap.guarantee),
            (python.status, python.radius, python.original_verdict, python.candidates,
             python.searched_up_to, python.guarantee))
        self.assertEqual(leap.witness, python.witness)
        self.assertTrue(r.verify(leap).valid)
        if leap.status == 'flipped':
            self.assertTrue(r.verify(leap).optimal)
        return leap

    def test_contract_and_verified_witness(self):
        rules = [rule('p', 'ALL', ['minor'], ['ex']),
                 rule('ex', 'ALL', ['essential', 'fair'])]
        answer = self.compare(rules, ['minor'], 'p')
        self.assertEqual((answer.radius, answer.witness),
                         (2, ('essential', 'fair')))
        self.assertTrue(answer.metadata['safe_shortcut'])
        self.assertEqual(answer.metadata['execution_mode'], 'structural_leap')

    def test_simple_false_to_true(self):
        answer = self.compare([rule('p', 'ANY', ['b', 'a'])], [], 'p')
        self.assertEqual(answer.witness, ('a',))

    def test_empty_conjunction_and_disjunction(self):
        for op in ('ALL', 'ANY'):
            with self.subTest(op=op):
                result = self.compare([rule('p', op)], [], 'p')
                self.assertEqual(result.status, 'stable')
                self.assertEqual(result.metadata['execution_mode'], 'structural_leap')

    def test_direct_target_leaf(self):
        rules = [rule('unrelated', 'ALL', ['x'])]
        self.assertEqual(self.compare(rules, [], 'z').witness, ('z',))
        self.assertEqual(self.compare(rules, ['z'], 'z').status, 'stable')

    def test_stable_with_addable_but_irrelevant_leaves(self):
        # A constant TRUE branch holds an OR rule TRUE for all 18 assignments.
        rules = [rule('p', 'ANY', ['always'] + ['f'+str(i) for i in range(18)]),
                 rule('always', 'ALL')]
        r = Reasoner(rules)
        result = r.analyze('p', method='leap')
        self.assertEqual(result.status, 'stable')
        self.assertEqual(len(result.candidates), 18)
        self.assertTrue(result.metadata['safe_shortcut'])
        # Independent exhaustive oracle only once; 2^18 worlds.
        self.assertEqual(result.status, r.challenge('p').status)

    def test_read_once_mixed_polarities(self):
        rules = [rule('p', 'ANY', ['a', 'q'], ['e']),
                 rule('q', 'ALL', ['b', 'c']),
                 rule('e', 'ANY', ['d', 'f'])]
        for facts in ((), ('a',), ('b',), ('a', 'd'), ('b', 'c', 'd')):
            with self.subTest(facts=facts):
                self.compare(rules, facts, 'p')

    def test_shared_leaf_must_fallback(self):
        cases = [
            [rule('p', 'ALL', ['x'], ['x'])],
            [rule('p', 'ANY', ['x', 'x'])],
            [rule('p', 'ALL', ['q'], ['x']), rule('q', 'ANY', ['x', 'y'])],
            [rule('p', 'ALL', ['q', 'q']), rule('q', 'ALL', ['x'])],
        ]
        for rules in cases:
            with self.subTest(rules=rules):
                result = self.compare(rules, [], 'p')
                self.assertEqual(result.metadata['execution_mode'], 'fallback_python')
                self.assertFalse(result.metadata['safe_shortcut'])

    def test_scope_and_budget(self):
        rules = [rule('p', 'ALL', ['a', 'b', 'c'])]
        for budget in (None, 0, 1, 2, 3, 4):
            with self.subTest(budget=budget):
                self.compare(rules, [], 'p', max_changes=budget)
        self.compare(rules, [], 'p', candidates=['a'])
        self.compare(rules, [], 'p', candidates=[])
        r = Reasoner(rules)
        for kw in ({'candidates': 'a'}, {'candidates': ['z']},
                   {'candidates': ['p']}, {'max_changes': -1},
                   {'max_changes': True}, {'fallback': 'invalid'},
                   {'z3_timeout_ms': 0}):
            with self.subTest(kw=kw), self.assertRaises(ValueError):
                r.analyze('p', method='leap', **kw)

    def test_600_differential_random_dags(self):
        # Includes shared children, nested exceptions, empty bodies, rule-head
        # shadowing and restricted candidates. Small leaf universe makes the
        # Python exhaustive method a feasible independent oracle.
        for seed in range(600):
            rng = random.Random(seed + 4000)
            leaves = ['f'+str(i) for i in range(6)]
            names = leaves[:]
            rules = []
            for i in range(6):
                rules.append(rule('p'+str(i), rng.choice(('ALL', 'ANY')),
                                  rng.choices(names, k=rng.randrange(0, 4)),
                                  rng.choices(names, k=rng.randrange(0, 3))))
                names.append('p'+str(i))
            facts = [f for f in leaves if rng.random() < 0.3]
            options = [f for f in leaves if f not in facts and f in Reasoner(rules, facts).graph.leaves('p5')]
            selected = [f for f in options if rng.random() < 0.7]
            scope = selected if seed % 3 == 0 else None
            cap = rng.randrange(0, 4) if seed % 4 == 0 else None
            with self.subTest(seed=seed):
                self.compare(rules, facts, 'p5', candidates=scope,
                             max_changes=cap)

    def test_400_differential_read_once_trees(self):
        # Independent generated trees force structural-leap coverage instead
        # of exercising only the fallback on random DAGs.
        for seed in range(400):
            rng = random.Random(seed + 7000)
            facts = ['f'+str(i) for i in range(8) if rng.random() < 0.4]
            pool = ['f'+str(i) for i in range(8)]
            rng.shuffle(pool)
            rules = []
            while len(pool) > 1:
                span = rng.randint(1, min(3, len(pool)))
                children = [pool.pop() for _ in range(span)]
                name = 'r'+str(len(rules))
                rng.shuffle(children)
                split = rng.randrange(0, len(children)+1)
                rules.append(rule(name, rng.choice(('ALL', 'ANY')),
                                  children[:split], children[split:]))
                pool.insert(rng.randrange(len(pool)+1), name)
            target = pool[0]
            with self.subTest(seed=seed):
                result = self.compare(rules, facts, target)
                self.assertTrue(result.metadata['safe_shortcut'])

    def test_large_read_once_bounded(self):
        leaves = ['f'+str(i) for i in range(1024)]
        r = Reasoner([rule('p', 'ALL', leaves)])
        result = r.analyze('p', method='leap', max_changes=8)
        self.assertEqual(result.status, 'budget_exceeded')
        self.assertEqual(result.metadata['execution_mode'], 'structural_leap')
        self.assertEqual(result.evaluations, 1)
        full = r.analyze('p', method='leap')
        self.assertEqual(full.radius, len(leaves))
        self.assertEqual(full.witness, tuple(sorted(leaves)))
        self.assertTrue(r.verify(full, verify_optimality=False).valid)

    def test_60_three_way_differential_z3_when_available(self):
        try:
            Z3Experiment._make_solver('auto')
        except RuntimeError:
            self.skipTest('Z3 solver is not available')
        from pythen import Z3ChallengeAnalyzer
        for seed in range(60):
            rng = random.Random(seed + 9900)
            names = ['f'+str(i) for i in range(5)]
            rules = []
            for i in range(5):
                rules.append(rule('p'+str(i), rng.choice(('ALL', 'ANY')),
                                  rng.choices(names, k=rng.randrange(0, 4)),
                                  rng.choices(names, k=rng.randrange(0, 3))))
                names.append('p'+str(i))
            facts = [f for f in names[:5] if rng.random() < 0.4]
            r = Reasoner(rules, facts).register(Z3ChallengeAnalyzer())
            results = [r.challenge('p4'),
                       r.analyze('p4', method='leap'),
                       r.analyze('p4', method='z3_challenge')]
            with self.subTest(seed=seed):
                self.assertEqual(len({(x.status, x.radius) for x in results}), 1)
                self.assertTrue(all(r.verify(x, verify_optimality=False).valid
                                    for x in results))

    def test_explicit_z3_fallback_if_available(self):
        try:
            Z3Experiment._make_solver('auto')
        except RuntimeError:
            self.skipTest('Z3 solver is not available')
        r = Reasoner([rule('p', 'ALL', ['x'], ['x'])])
        output = r.analyze('p', method='leap', fallback='z3')
        self.assertEqual(output.status, 'stable')
        self.assertEqual(output.metadata['execution_mode'], 'fallback_z3')
        self.assertTrue(r.verify(output).valid)


if __name__ == '__main__':
    unittest.main()
