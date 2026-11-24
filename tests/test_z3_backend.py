"""Differential tests: optional Z3 solvers vs independent Python reference.

The same battery runs against the default auto-resolved engine and against
the forced ctypes engine, so encoding drift between the two adapters is
caught. Engines that are not usable on the host are skipped with a reason.
"""
import random
import unittest

from pythen import Reasoner, Z3ChallengeAnalyzer
from pythen.solvers.z3_native import Z3Experiment


def rule(p, op='ALL', conditions=(), exceptions=()):
    return {'p':p, 'op':op, 'conditions':list(conditions), 'exceptions':list(exceptions)}


def _engine_available(engine):
    try:
        Z3Experiment._make_solver(engine)
        return True
    except RuntimeError:
        return False


class Z3BackendMixin:
    engine = 'auto'

    def assess(self, rules, facts, target, candidates=None, max_changes=None, check_certificate=True):
        reasoner=Reasoner(rules, facts)
        reasoner.register(Z3ChallengeAnalyzer(engine=self.engine))
        oracle=reasoner.challenge(target,candidates=candidates,max_changes=max_changes)
        sat=reasoner.analyze(target,method='z3_challenge',candidates=candidates,max_changes=max_changes)
        self.assertEqual((sat.original_verdict,sat.status,sat.radius),
                         (oracle.original_verdict,oracle.status,oracle.radius))
        self.assertTrue(reasoner.verify(sat).valid)
        if sat.status=='flipped':
            self.assertEqual(sat.radius,len(sat.witness))
            self.assertNotEqual(reasoner.evaluate(target),reasoner.with_facts(reasoner.facts.union(sat.witness)).evaluate(target))
            self.assertTrue(reasoner.verify(sat).optimal)
            if sat.radius > 0 and check_certificate:
                # Independently ask SMT to prove no smaller additive intervention exists.
                z=Z3Experiment(reasoner.graph, engine=self.engine)
                self.assertTrue(z.prove_no_smaller(reasoner.facts,target,candidates,cap=sat.radius-1))
        return sat

    def test_simple_witness(self):
        x=self.assess([rule('p','ALL',['minor'],['ex']),rule('ex','ALL',['essential','fair'])],['minor'],'p')
        self.assertEqual(x.radius,2)
        self.assertEqual(x.witness,('essential','fair'))

    def test_shared_contradiction_stable(self):
        self.assess([rule('x','ANY',['a','b']),rule('p','ALL',['x'],['x'])],[],'p')

    def test_all_empty_stable(self):
        self.assess([rule('p','ALL',[])],[],'p')

    def test_any_empty_stable(self):
        self.assess([rule('p','ANY',[])],[],'p')

    def test_leaf_target_absent(self):
        self.assess([rule('q','ALL',['x'])],[],'z')

    def test_leaf_target_present(self):
        self.assess([rule('q','ALL',['x'])],['z'],'z')

    def test_fact_shadowed_by_derived_head(self):
        self.assess([rule('p','ALL',['x'])],['p'],'p')

    def test_candidate_restriction(self):
        self.assess([rule('p','ANY',['a','b','c'])],[],'p',candidates=['b'])
        self.assess([rule('p','ANY',['a','b','c'])],[],'p',candidates=[])

    def test_bounded(self):
        rules=[rule('p','ALL',['minor'],['ex']),rule('ex','ALL',['x','y'])]
        self.assess(rules,['minor'],'p',max_changes=0)
        self.assess(rules,['minor'],'p',max_changes=1)
        self.assess(rules,['minor'],'p',max_changes=2)

    def test_nested_rules(self):
        self.assess([rule('p','ANY',['a','b'],['e']),rule('e','ANY',['x','y'],['sub']),rule('sub','ALL',['q','r'])],['a','x'],'p')

    def test_80_random_oracles(self):
        for seed in range(80):
            rng=random.Random(seed)
            names=['f'+str(i) for i in range(6)]
            rules=[]
            for i in range(7):
                rules.append(rule('p'+str(i),rng.choice(['ALL','ANY']),
                                  rng.sample(names,rng.randrange(0,min(4,len(names)))),
                                  rng.sample(names,rng.randrange(0,min(3,len(names))))))
                names.append('p'+str(i))
            facts=[x for x in names[:6] if rng.random()<0.25]
            with self.subTest(seed=seed):
                self.assess(rules,facts,'p6',check_certificate=False)


@unittest.skipUnless(_engine_available('z3py') or _engine_available('ctypes'),
                     'no usable Z3 engine found')
class Z3BackendTests(Z3BackendMixin, unittest.TestCase):
    """Default auto-resolved engine (z3py preferred, ctypes fallback)."""


@unittest.skipUnless(_engine_available('ctypes'),
                     'system libz3 with SMT-LIB optimization support not available')
class Z3CtypesBackendTests(Z3BackendMixin, unittest.TestCase):
    engine = 'ctypes'


class Z3InterfaceTests(unittest.TestCase):
    def test_invalid_engine_rejected(self):
        with self.assertRaises(ValueError):
            Z3Experiment(None, engine='cplex')

    def test_unsupported_libz3_reports_clear_error(self):
        # On hosts whose apt libz3 (4.8.x) cannot handle SMT-LIB optimization,
        # the ctypes engine must raise an actionable message, not fail later
        # with "unexpected Z3 output".
        import ctypes.util
        if _engine_available('ctypes'):
            self.skipTest('this libz3 supports SMT-LIB optimization')
        if ctypes.util.find_library('z3') is None:
            self.skipTest('no libz3 present to probe')
        r=Reasoner([rule('p','ALL',['a'])],['b'])
        with self.assertRaises(RuntimeError) as cm:
            Z3Experiment(r.graph, engine='ctypes')
        message=str(cm.exception)
        self.assertIn('optimization', message)
        self.assertIn('pythen[z3]', message)


if __name__ == '__main__':
    unittest.main()
