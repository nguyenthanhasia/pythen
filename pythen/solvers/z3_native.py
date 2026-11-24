"""Optional Z3 SMT backends for PYTHEN 2 (experimental).

Engines, in preference order:

- ``z3py``: the official Z3 Python bindings, driving the ``Optimize`` API
  directly. Preferred adapter (see docs/z3_backend.md).
- ``ctypes``: fallback that loads a system ``libz3`` shared library and talks
  to it through ``Z3_eval_smtlib2_string``. This text evaluator only accepts
  SMT-LIB optimization commands on newer builds (verified on Z3 5.x); the
  Ubuntu/Debian apt ``libz3`` 4.8.x silently answers ``unsupported`` and is
  **not usable**. A capability probe at load time now raises a clear,
  actionable ``RuntimeError`` instead of a confusing solver failure.

The regular Python backend remains the default; neither engine is selected
automatically. Semantics: acyclic Pythen DAG, closed-world Boolean leaves,
addition-only changes. Encoding is Python; only the solver call is native.
"""
import ctypes
import ctypes.util
import re
import time
from dataclasses import dataclass
from typing import Optional, Tuple


@dataclass(frozen=True)
class SolverAnswer:
    status: str
    radius: Optional[int]
    witness: Tuple[str, ...]
    original_verdict: bool
    wall_seconds: float
    script_bytes: int


def _version_text(version):
    return '.'.join(str(x) for x in version)


class Z3PySolver:
    """Official Z3 Python bindings adapter using the Optimize API."""

    name = 'z3py'

    def __init__(self):
        try:
            import z3
        except ImportError as exc:
            raise RuntimeError(
                "z3py bindings not installed; use pip install 'pythen[z3]' "
                "(or pip install z3-solver)"
            ) from exc
        self.z3 = z3
        self.version = tuple(int(x) for x in z3.get_version_string().split('.')[:3])


class NativeZ3:
    """System libz3 via ctypes, driven with SMT-LIB text scripts."""

    name = 'ctypes-libz3'

    def __init__(self):
        libname = ctypes.util.find_library("z3")
        if libname is None:
            raise RuntimeError("Z3 system library not found")
        self.library = libname
        z = ctypes.CDLL(libname)
        self.z = z
        z.Z3_mk_config.restype = ctypes.c_void_p
        z.Z3_mk_context.argtypes = [ctypes.c_void_p]
        z.Z3_mk_context.restype = ctypes.c_void_p
        z.Z3_del_config.argtypes = [ctypes.c_void_p]
        z.Z3_del_context.argtypes = [ctypes.c_void_p]
        z.Z3_eval_smtlib2_string.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
        z.Z3_eval_smtlib2_string.restype = ctypes.c_char_p
        z.Z3_get_version.argtypes = [
            ctypes.POINTER(ctypes.c_uint), ctypes.POINTER(ctypes.c_uint),
            ctypes.POINTER(ctypes.c_uint), ctypes.POINTER(ctypes.c_uint)]
        z.Z3_get_version.restype = None
        major, minor, build, rev = (ctypes.c_uint(), ctypes.c_uint(),
                                    ctypes.c_uint(), ctypes.c_uint())
        z.Z3_get_version(ctypes.byref(major), ctypes.byref(minor),
                         ctypes.byref(build), ctypes.byref(rev))
        self.version = (major.value, minor.value, build.value)
        self._probe_optimize()

    def _probe_optimize(self):
        # Reject libraries whose text evaluator answers "unsupported" to
        # optimization commands before any real query is attempted.
        probe = ("(declare-const _pythen_probe_a Bool)\n"
                 "(declare-const _pythen_probe_b Bool)\n"
                 "(assert (or _pythen_probe_a _pythen_probe_b))\n"
                 "(minimize (+ (ite _pythen_probe_a 1 0) (ite _pythen_probe_b 1 0)))\n"
                 "(check-sat)")
        out = self.run(probe)
        if 'unsupported' in out:
            raise RuntimeError(
                "system libz3 {} ({}) does not support SMT-LIB optimization "
                "commands (minimize/maximize) through the ctypes text evaluator. "
                "Install the official Python bindings (pip install 'pythen[z3]') "
                "or a Z3 build whose text evaluator supports optimization "
                "(tested with Z3 5.x; the Ubuntu/Debian apt libz3 4.8.x does "
                "not). PYTHEN's pure-Python challenge() remains available."
                .format(_version_text(self.version), self.library))
        if not out.startswith('sat'):
            raise RuntimeError(
                "system libz3 {} ({}) failed the optimization capability probe: {}"
                .format(_version_text(self.version), self.library, out[:120]))

    def run(self, script: str) -> str:
        z = self.z
        cfg = z.Z3_mk_config()
        ctx = z.Z3_mk_context(cfg)
        z.Z3_del_config(cfg)
        try:
            # Z3 raises a hard C-level error if get-value is requested on UNSAT.
            # Query status first, then request a model only when SAT was proven.
            parts = script.split("\n(get-value ", 1)
            main = parts[0]
            result = z.Z3_eval_smtlib2_string(ctx, main.encode("utf-8"))
            if not result:
                raise RuntimeError("No Z3 response")
            status = result.decode("utf-8").strip()
            if not status.startswith("sat") or len(parts) < 2:
                return status
            values = z.Z3_eval_smtlib2_string(ctx, ("(get-value " + parts[1]).encode("utf-8"))
            if not values:
                raise RuntimeError("Missing model response")
            return status + "\n" + values.decode("utf-8")
        finally:
            z.Z3_del_context(ctx)


class Z3Experiment:
    def __init__(self, graph, timeout_ms: int = 15000, engine: str = 'auto'):
        self.graph = graph
        self.timeout_ms = timeout_ms
        self.solver = self._make_solver(engine)
        self.engine = self.solver.name

    @staticmethod
    def _make_solver(engine: str):
        if engine not in ('auto', 'z3py', 'ctypes'):
            raise ValueError("invalid engine; use 'auto', 'z3py' or 'ctypes'")
        ctypes_error = None
        if engine in ('auto', 'z3py'):
            try:
                return Z3PySolver()
            except RuntimeError:
                if engine == 'z3py':
                    raise
        if engine in ('auto', 'ctypes'):
            try:
                return NativeZ3()
            except RuntimeError as exc:
                if engine == 'ctypes':
                    raise
                ctypes_error = exc
            else:
                return NativeZ3()
        raise RuntimeError(
            "no usable Z3 engine: " + (str(ctypes_error) if ctypes_error else
            "z3py bindings and system libz3 are both unavailable; "
            "install with pip install 'pythen[z3]'"))

    # ---- encoding (single naming pass, two renderers) ----

    def _prepare(self, facts, target, candidates):
        graph = self.graph
        if not isinstance(target, str) or not target:
            raise ValueError("invalid target")
        facts = frozenset(facts)
        available = set(graph.leaves(target)) - facts
        if candidates is None:
            options = tuple(sorted(available))
        else:
            options = tuple(sorted(set(candidates)))
            if not set(options) <= available:
                raise ValueError("invalid candidates")
        # Map arbitrary user strings onto safe SMT variable names.
        heads = tuple(sorted(graph.nodes))
        leaves = graph.leaves() + ((target,) if target not in graph.nodes and target not in graph.leaves() else ())
        all_names = tuple(sorted(set(heads) | set(leaves)))
        var = {name: 'v' + str(i) for i, name in enumerate(all_names)}
        return facts, options, all_names, var

    def compile(self, facts, target: str, candidates=None, optimize=True, cap=None):
        graph = self.graph
        facts, options, all_names, var = self._prepare(facts, target, candidates)

        def conj(xs):
            return "true" if not xs else "(and " + " ".join(xs) + ")"

        def disj(xs):
            return "false" if not xs else "(or " + " ".join(xs) + ")"

        lines = ["(set-option :produce-models true)", f"(set-option :timeout {self.timeout_ms})"]
        lines.extend(f"(declare-const {var[name]} Bool)" for name in all_names)

        for name in sorted(graph.nodes):
            node = graph.nodes[name]
            body = conj([var[x] for x in node.conditions]) if node.op == 'ALL' else disj([var[x] for x in node.conditions])
            excepts = disj([var[x] for x in node.exceptions])
            lines.append(f"(assert (= {var[name]} (and {body} (not {excepts}))))")
        for leaf in all_names:
            if leaf in graph.nodes:
                continue
            if leaf in facts:
                lines.append(f"(assert {var[leaf]})")
            elif leaf not in options:
                lines.append(f"(assert (not {var[leaf]}))")
        if optimize:
            original = graph.evaluate(facts, target)
            lines.append(f"(assert {'(not '+var[target]+')' if original else var[target]})")
            if options:
                count = "(+ " + " ".join(f"(ite {var[x]} 1 0)" for x in options) + ")"
                lines.append("(minimize " + count + ")")
                if cap is not None:
                    lines.append(f"(assert (<= {count} {cap}))")
        lines.append("(check-sat)")
        if options:
            lines.append("(get-value (" + " ".join(var[x] for x in options) + "))")
        elif not optimize:
            lines.append("(get-value (" + var[target] + "))")
        return "\n".join(lines), options, var

    def _optimize(self, facts, target, options, var, want_flip, cap):
        """Build the same problem on the Optimize API (z3py path)."""
        graph = self.graph
        z3mod = self.solver.z3
        opt = z3mod.Optimize()
        opt.set('timeout', self.timeout_ms)
        expr = {name: z3mod.Bool(var[name]) for name in var}
        for name in sorted(graph.nodes):
            node = graph.nodes[name]
            conditions = tuple(node.conditions)
            exceptions = tuple(node.exceptions)
            if node.op == 'ALL':
                body = z3mod.And(*[expr[x] for x in conditions]) if conditions else z3mod.BoolVal(True)
            else:
                body = z3mod.Or(*[expr[x] for x in conditions]) if conditions else z3mod.BoolVal(False)
            excepts = z3mod.Or(*[expr[x] for x in exceptions]) if exceptions else z3mod.BoolVal(False)
            opt.add(expr[name] == z3mod.And(body, z3mod.Not(excepts)))
        option_set = set(options)
        for leaf in var:
            if leaf in graph.nodes:
                continue
            if leaf in facts:
                opt.add(expr[leaf])
            elif leaf not in option_set:
                opt.add(z3mod.Not(expr[leaf]))
        if want_flip is not None:
            opt.add(z3mod.Not(expr[target]) if want_flip else expr[target])
            if options:
                count = sum(z3mod.If(expr[x], 1, 0) for x in options)
                if cap is not None:
                    opt.add(count <= cap)
                opt.minimize(count)
        return opt, expr

    # ---- queries ----

    def challenge(self, facts, target, candidates=None, max_changes=None):
        if max_changes is not None and (type(max_changes) is not int or max_changes < 0):
            raise ValueError("invalid max_changes")
        start = time.perf_counter()
        script, options, var = self.compile(facts, target, candidates, optimize=True)
        prepared = self._prepare(facts, target, candidates)
        original = self.graph.evaluate(prepared[0], target)
        if self.solver.name == 'z3py':
            opt, expr = self._optimize(*prepared[:1] + (target, prepared[1], prepared[3]),
                                       want_flip=original, cap=max_changes)
            result = opt.check()
            z3mod = self.solver.z3
            if result == z3mod.unknown:
                raise TimeoutError("Z3 reported unknown: " + str(opt.reason_unknown())[:300])
            if result == z3mod.unsat:
                status, selected = 'unsat', None
            else:
                model = opt.model()
                status = 'sat'
                selected = tuple(x for x in options
                                 if z3mod.is_true(model.evaluate(expr[x], model_completion=True)))
        else:
            output = self.solver.run(script).strip()
            if output.startswith('unknown'):
                raise TimeoutError("Z3 reported unknown: " + output[:300])
            if output.startswith('unsat'):
                status, selected = 'unsat', None
            elif not output.startswith('sat'):
                raise RuntimeError("unexpected Z3 output: " + output[:300])
            else:
                status = 'sat'
                selected = tuple(x for x in options if re.search(r'\(' + var[x] + r'\s+true\)', output))
        return self._finalize_challenge(status, selected, options, max_changes,
                                        facts, target, start, len(script))

    def _finalize_challenge(self, status, selected, options, max_changes, facts, target,
                            start, script_bytes):
        if status == 'unsat':
            verdict = 'stable' if max_changes is None or max_changes >= len(options) else 'budget_exceeded'
            return SolverAnswer(verdict, None, (), self.graph.evaluate(facts, target),
                                time.perf_counter() - start, script_bytes)
        n = len(selected)
        limit = len(options) if max_changes is None else min(len(options), max_changes)
        if n > limit:
            return SolverAnswer('budget_exceeded', None, (), self.graph.evaluate(facts, target),
                                time.perf_counter() - start, script_bytes)
        base = self.graph.evaluate(facts, target)
        if self.graph.evaluate(frozenset(facts).union(selected), target) == base:
            raise AssertionError("model witness did not flip target")
        return SolverAnswer('flipped', n, selected, base, time.perf_counter() - start, script_bytes)

    def prove_no_smaller(self, facts, target, candidates=None, cap=None):
        """True when no addition-only witness of size <= cap flips the verdict."""
        if self.solver.name == 'z3py':
            _, options, _, var = self._prepare(facts, target, candidates)
            original = self.graph.evaluate(frozenset(facts), target)
            opt, _ = self._optimize(frozenset(facts), target, options, var,
                                    want_flip=original, cap=cap)
            result = opt.check()
            if result == self.solver.z3.unknown:
                raise TimeoutError("Z3 reported unknown: " + str(opt.reason_unknown())[:300])
            return result == self.solver.z3.unsat
        script, _, _ = self.compile(facts, target, candidates, optimize=True, cap=cap)
        output = self.solver.run(script).strip()
        if output.startswith('unknown'):
            raise TimeoutError("Z3 reported unknown: " + output[:300])
        if output.startswith('unsat'):
            return True
        if not output.startswith('sat'):
            raise RuntimeError("unexpected Z3 output: " + output[:300])
        return False

    def evaluate(self, facts, target):
        start = time.perf_counter()
        script, _, var = self.compile(facts, target, candidates=(), optimize=False)
        if self.solver.name == 'z3py':
            prepared = self._prepare(facts, target, ())
            opt, expr = self._optimize(*prepared[:1] + (target, prepared[1], prepared[3]),
                                       want_flip=None, cap=None)
            result = opt.check()
            z3mod = self.solver.z3
            if result != z3mod.sat:
                raise RuntimeError('bad evaluation result ' + str(result))
            ans = z3mod.is_true(opt.model().evaluate(expr[target], model_completion=True))
            return ans, time.perf_counter() - start
        output = self.solver.run(script).strip()
        if not output.startswith('sat'):
            raise RuntimeError('bad evaluation output ' + output[:200])
        ans = bool(re.search(r'\(' + var[target] + r'\s+true\)', output))
        return ans, time.perf_counter() - start


from ..analysis import Analyzer


class Z3ChallengeAnalyzer(Analyzer):
    """Opt-in Z3/SMT implementation of the v2 challenge analyzer.

    Prefers the official z3py bindings (``pip install 'pythen[z3]'``) and
    falls back to a loadable system libz3 through ``ctypes`` when the text
    evaluator supports SMT-LIB optimization. This is an experimental optional
    backend; pass ``engine='z3py'`` or ``engine='ctypes'`` to force one.
    """
    name = 'z3_challenge'

    def __init__(self, engine: str = 'auto', timeout_ms: int = 15000):
        self.engine = engine
        self.timeout_ms = timeout_ms

    def analyze(self, context, candidates=None, max_changes=None):
        from ..analysis import AnalysisResult
        backend = Z3Experiment(context.graph, timeout_ms=self.timeout_ms, engine=self.engine)
        output = backend.challenge(context.evidence.facts, context.target, candidates, max_changes)
        allowed = set(context.graph.leaves(context.target)) - context.evidence.facts
        options = tuple(sorted(allowed if candidates is None else set(candidates)))
        limit = len(options) if max_changes is None else min(len(options), max_changes)
        size = output.radius
        return AnalysisResult(
            method=self.name,
            target=context.target,
            original_verdict=output.original_verdict,
            status=output.status,
            radius=size,
            witness=output.witness,
            candidates=options,
            evaluations=1,
            searched_up_to=(size if output.status == 'flipped' else
                            len(options) if output.status == 'stable' else limit),
            guarantee=('optimal' if output.status == 'flipped' else
                       'exhaustive' if output.status == 'stable' else 'bounded'),
            metadata={
                'engine': backend.engine,
                'z3_version': _version_text(backend.solver.version),
                'experimental': True,
                'solving': 'SMT Optimize',
                'intervention': 'add_only',
                'universe': 'reachable_leaf_facts',
                'solver_wall_seconds': output.wall_seconds,
                'smt_script_bytes': output.script_bytes,
                'solver_invocations': 1,
            },
        )
