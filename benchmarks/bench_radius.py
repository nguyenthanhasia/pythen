"""Deterministic tiny-scale baseline CSV for the PYTHEN 2 framework.

Not a scientific evaluation on its own. Use external datasets and baselines
before drawing conclusions about speed or generality.
"""
import argparse
import csv
import random
import sys
import time
from pythen import Reasoner


def generate(seed, leaves=8, rules=6):
    rng = random.Random(seed)
    predicates = ["f" + str(i) for i in range(leaves)]
    result = []
    for i in range(rules):
        options = predicates[:]
        conditions = rng.sample(options, rng.randrange(min(len(options), 3) + 1))
        exceptions = rng.sample(options, rng.randrange(min(len(options), 2) + 1))
        result.append({"p": "p" + str(i), "op": rng.choice(["ALL", "ANY"]),
                       "conditions": conditions, "exceptions": exceptions})
        predicates.append("p" + str(i))
    facts = ["f" + str(i) for i in range(leaves) if rng.choice([False, True])]
    return result, facts, "p" + str(rules - 1)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases", type=int, default=30)
    parser.add_argument("--leaves", type=int, default=8)
    parser.add_argument("--rules", type=int, default=6)
    parser.add_argument("--seed", type=int, default=2026)
    parser.add_argument("--max-changes", type=int, default=None)
    args = parser.parse_args()
    if args.cases < 0 or args.leaves < 1 or args.rules < 1:
        parser.error("cases >= 0, leaves >= 1, rules >= 1 are required")
    writer = csv.writer(sys.stdout)
    writer.writerow(["case", "graph_sha256", "target", "leaves", "status", "radius", "witness", "evaluations", "elapsed_seconds"])
    for i in range(args.cases):
        rules, facts, target = generate(args.seed + i, args.leaves, args.rules)
        reasoner = Reasoner(rules, facts)
        start = time.perf_counter()
        result = reasoner.challenge(target, max_changes=args.max_changes)
        elapsed = time.perf_counter() - start
        assert reasoner.verify(result).valid
        writer.writerow([i, reasoner.graph.fingerprint, target,
                         len(reasoner.graph.leaves(target)), result.status,
                         result.radius if result.radius is not None else "",
                         ";".join(result.witness), result.evaluations,
                         "{:.8f}".format(elapsed)])


if __name__ == "__main__":
    main()
