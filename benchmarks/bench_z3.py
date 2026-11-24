"""Reproducible baseline vs experimental Z3 benchmark. No public integration."""
import argparse
import csv
import json
import os
import platform
import random
import statistics
import sys
import time
from pathlib import Path
from pythen import Reasoner
from pythen.solvers.z3_native import Z3Experiment


def rule(p, op, conditions, exceptions=()):
    return {'p': p, 'op': op, 'conditions': list(conditions), 'exceptions': list(exceptions)}


def backend(graph, engine):
    return Z3Experiment(graph, engine=engine)


def make_case(case, n, k=0):
    leaves = ['e%03d' % i for i in range(n)]
    if case == 'easy':
        rules = [rule('target', 'ANY', leaves)]
        facts = ()
    elif case == 'hard':
        # Every candidate reachable but only first k relevant to the flip.
        # Base has minor and known; exception must activate all k required facts.
        assert 1 <= k <= n
        rules = [rule('target', 'ALL', ['minor'], ['exception']),
                 rule('exception', 'ALL', leaves[:k] + ['gate']),
                 rule('gate', 'ANY', ['known'] + leaves[k:])]
        facts = ('minor','known')
    elif case == 'stable':
        # Non-monotonic shared dependency makes verdict forever false.
        rules = [rule('anyleaf', 'ANY', leaves),
                 rule('target', 'ALL', ['anyleaf'], ['anyleaf'])]
        facts = ()
    elif case == 'bounded':
        assert 1 <= k <= n
        rules = [rule('target', 'ALL', ['minor'], ['exception']),
                 rule('exception', 'ALL', leaves[:k] + ['gate']),
                 rule('gate', 'ANY', ['known'] + leaves[k:])]
        facts = ('minor','known')
    else:
        raise ValueError(case)
    return Reasoner(rules, facts), 'target'


def random_case(seed, num_leaves=8, num_rules=10):
    rng = random.Random(seed)
    symbols=['f'+str(i) for i in range(num_leaves)]
    rules=[]
    for i in range(num_rules):
        arity=rng.randint(0, min(3, len(symbols)))
        exc=rng.randint(0, min(2, len(symbols)))
        rules.append(rule('p'+str(i), rng.choice(['ALL','ANY']),
                          rng.sample(symbols, arity), rng.sample(symbols, exc)))
        symbols.append('p'+str(i))
    facts=[x for x in symbols[:num_leaves] if rng.random() < 0.3]
    return Reasoner(rules, facts), 'p'+str(num_rules-1)


def validate(num_random=240, engine='auto'):
    count=0
    for seed in range(num_random):
        r, target = random_case(seed, 7, 9)
        b=backend(r.graph, engine)
        for limit in (None, 0, 1, 2):
            a=r.challenge(target,max_changes=limit)
            c=b.challenge(r.facts,target,max_changes=limit)
            if (a.status,a.radius,a.original_verdict)!=(c.status,c.radius,c.original_verdict):
                raise AssertionError(f'mismatch {seed} limit {limit} {a} {c}')
            if c.status=='flipped':
                assert r.with_facts(r.facts.union(c.witness)).evaluate(target) != c.original_verdict
                assert len(c.witness)==c.radius
            count+=1
        zz,_=b.evaluate(r.facts,target)
        assert zz == r.evaluate(target)
    return count


def run_case(case,n,k,limit,repeats,engine='auto'):
    r,target=make_case(case,n,k)
    b=backend(r.graph, engine)
    bs_times=[]; sat_times=[]
    py_results=[]; sat_results=[]
    for _ in range(repeats):
        start=time.perf_counter()
        a=r.challenge(target,max_changes=limit)
        bs_times.append(time.perf_counter()-start)
        start=time.perf_counter()
        c=b.challenge(r.facts,target,max_changes=limit)
        sat_times.append(time.perf_counter()-start)
        assert (a.status,a.radius,a.original_verdict)==(c.status,c.radius,c.original_verdict)
        assert c.status!='flipped' or r.with_facts(r.facts.union(c.witness)).evaluate(target)!=c.original_verdict
        py_results.append(a);sat_results.append(c)
    return {
        'case':case,'leaves':n,'k':k,'max_changes':limit,'repeats':repeats,
        'engine':b.engine,'z3_version':'.'.join(map(str,b.solver.version)),
        'baseline_ms':round(statistics.median(bs_times)*1000,4),
        'z3_ms':round(statistics.median(sat_times)*1000,4),
        'speedup_baseline_over_z3':round(statistics.median(bs_times)/statistics.median(sat_times),3),
        'status':py_results[0].status,'radius':py_results[0].radius,
        'baseline_evaluations':py_results[0].evaluations,
        'smt_script_bytes':sat_results[0].script_bytes
    }


def eval_case(n, repeats=100, engine='auto'):
    r,target=make_case('easy',n)
    b=backend(r.graph, engine)
    # Compare each backend's actual per-query cost; compiled RuleGraph already exists.
    data=[tuple('e%03d'%i for i in range(n) if ((i*71 + j*41) % 17 < 5)) for j in range(repeats)]
    start=time.perf_counter()
    expected=[r.graph.evaluate(f,target) for f in data]
    pure=(time.perf_counter()-start)/repeats
    start=time.perf_counter()
    actual=[b.evaluate(f,target)[0] for f in data]
    solver=(time.perf_counter()-start)/repeats
    assert expected==actual
    return {'case':'evaluate','leaves':n,'k':None,'max_changes':None,'repeats':repeats,
            'engine':b.engine,'z3_version':'.'.join(map(str,b.solver.version)),
            'baseline_ms':round(pure*1000,5),'z3_ms':round(solver*1000,5),
            'speedup_baseline_over_z3':round(pure/solver,4),'status':'passed','radius':None,
            'baseline_evaluations':repeats,'smt_script_bytes':0}


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--output',default='results')
    p.add_argument('--random',type=int,default=240)
    p.add_argument('--engine',default='auto',choices=['auto','z3py','ctypes'])
    args=p.parse_args()
    folder=Path(args.output);folder.mkdir(parents=True,exist_ok=True)
    checked=validate(args.random, args.engine)
    cases=[]
    for case,n,k,limit,repeats in [
        ('easy',8,0,None,7),('easy',32,0,None,7),('easy',128,0,None,5),
        ('hard',12,3,None,5),('hard',22,4,None,3),('hard',30,5,None,1),
        ('stable',10,0,None,5),('stable',14,0,None,3),('stable',17,0,None,1),
        ('bounded',40,5,2,3),('bounded',80,6,3,1),
    ]:
        row=run_case(case,n,k,limit,repeats,args.engine)
        print(json.dumps(row),flush=True)
        cases.append(row)
    for n in [8,32,128]:
        row=eval_case(n,60 if n<=32 else 20,args.engine)
        print(json.dumps(row),flush=True)
        cases.append(row)
    fn=folder/'benchmark.csv'
    with fn.open('w',newline='',encoding='utf8') as f:
        w=csv.DictWriter(f,fieldnames=list(cases[0]));w.writeheader();w.writerows(cases)
    audit={
        'environment':{'python':sys.version,'platform':platform.platform(),
                       'engine_requested':args.engine,
                       'engines_observed':sorted({row['engine'] for row in cases}),
                       'library':'z3py bindings or system libz3 via ctypes, resolved per engine',
                       'cpu':platform.processor()},
        'random_graph_checks':checked,
        'cases':cases,
        'interpretation':'This tests the Z3 SMT optimizer through the selected adapter (official z3py Optimize API, or the ctypes SMT-LIB text evaluator on builds that support optimization commands). Wall times include encoding and solver context creation. No hot-path engine switch is implied.'
    }
    (folder/'audit.json').write_text(json.dumps(audit,indent=2),encoding='utf8')
    print('VALIDATED',checked,'random checks; CSV:',fn)

if __name__=='__main__':
    main()
