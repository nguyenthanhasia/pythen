"""Reproducible Python/Z3/Leap cold-query latency comparisons.

Uses identical graph + evidence + target for each method, includes analyzer
initialization for Z3 and challenge query overhead for all three. This is a
microbenchmark of specified workloads, not an overall speedup claim.

    python benchmarks/bench_leap.py --repeats 5 --output benchmarks/results/leap_local.csv
"""
import argparse
import csv
import platform
import statistics
import sys
import time

from pythen import Reasoner, Z3ChallengeAnalyzer
from pythen.solvers.z3_native import Z3Experiment


def rule(p, op='ALL', conditions=(), exceptions=()):
    return {'p': p, 'op': op, 'conditions': list(conditions),
            'exceptions': list(exceptions)}


def workloads():
    # The expected minimum additions are set by construction, not by the solver.
    easy = (Reasoner([rule('p', 'ANY', ['a', 'b', 'c'])]), 'p', None)
    groups = []
    for j in range(5):
        groups.append(rule('g'+str(j), 'ALL', ['f'+str(5*j+i) for i in range(5)]))
    groups.append(rule('p', 'ANY', ['g'+str(j) for j in range(5)]))
    high_radius = (Reasoner(groups), 'p', None)
    # Even with many missing facts, the constant TRUE branch makes p stable.
    stable = (Reasoner([rule('always', 'ALL'),
                        rule('p', 'ANY', ['always'] + ['f'+str(i) for i in range(16)])]),
              'p', None)
    # A shared fact makes independent min-plus composition unsound.
    shared = (Reasoner([rule('p', 'ALL', ['x'], ['x'])]), 'p', None)
    # Large bounded case: impossible to flip at <=2, but a full Python
    # minimum-cardinality search is deliberately not attempted here.
    bounded = (Reasoner([rule('p', 'ALL', ['f'+str(i) for i in range(128)])]),
               'p', 2)
    return [('easy_radius_1', *easy), ('read_once_radius_5', *high_radius),
            ('read_once_stable_16', *stable), ('shared_dependency', *shared),
            ('read_once_128_bounded_2', *bounded)]


def measure(fn, repeats):
    timings = []
    answer = None
    for _ in range(repeats):
        started = time.perf_counter()
        answer = fn()
        timings.append((time.perf_counter() - started) * 1000)
    return answer, statistics.median(timings), min(timings), max(timings)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--repeats', type=int, default=5)
    parser.add_argument('--output', type=str, default=None)
    args = parser.parse_args()
    if args.repeats < 1:
        parser.error('--repeats must be positive')
    try:
        Z3Experiment._make_solver('auto')
        have_z3 = True
    except RuntimeError:
        have_z3 = False
    rows = []
    for name, r, target, limit in workloads():
        def python_query():
            return r.challenge(target, max_changes=limit)
        def leap_query():
            return r.analyze(target, method='leap', max_changes=limit)
        original, py_ms, py_min, py_max = measure(python_query, args.repeats)
        leap, leap_ms, leap_min, leap_max = measure(leap_query, args.repeats)
        assert (original.status, original.radius, original.original_verdict) == (
            leap.status, leap.radius, leap.original_verdict)
        assert r.verify(leap, verify_optimality=False).valid
        measurements = [
            ('python', original, py_ms, py_min, py_max),
            ('leap', leap, leap_ms, leap_min, leap_max),
        ]
        if have_z3:
            # Construct once at setup, like a Reasoner with registered plugin.
            r.register(Z3ChallengeAnalyzer(engine='auto'))
            def z3_query():
                return r.analyze(target, method='z3_challenge', max_changes=limit)
            z3, z3_ms, z3_min, z3_max = measure(z3_query, args.repeats)
            assert (original.status, original.radius, original.original_verdict) == (
                z3.status, z3.radius, z3.original_verdict)
            assert r.verify(z3, verify_optimality=False).valid
            measurements.append(('z3', z3, z3_ms, z3_min, z3_max))
        for method, result, median, low, high in measurements:
            rows.append({
                'workload': name, 'method': method,
                'status': result.status, 'radius': '' if result.radius is None else result.radius,
                'median_ms': '%.6f' % median, 'min_ms': '%.6f' % low,
                'max_ms': '%.6f' % high, 'runs': args.repeats,
                'execution_mode': result.metadata.get('execution_mode', method),
                'python_version': platform.python_version(),
                'system': platform.system(),
                'graph_sha256': r.graph.fingerprint,
            })
    if args.output:
        with open(args.output, 'w', newline='', encoding='utf-8') as fp:
            writer = csv.DictWriter(fp, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)
    print('workload'.ljust(30), 'python ms'.rjust(12), 'leap ms'.rjust(12),
          'z3 ms'.rjust(12), 'mode')
    for name, _, _, _ in workloads():
        record = {x['method']: x for x in rows if x['workload'] == name}
        print(name.ljust(30), *(record[k]['median_ms'].rjust(12) if k in record
              else 'n/a'.rjust(12) for k in ('python', 'leap', 'z3')),
              record['leap']['execution_mode'])
    if not have_z3:
        print('Z3 not available on this host: Z3 benchmarks skipped.', file=sys.stderr)


if __name__ == '__main__':
    main()
