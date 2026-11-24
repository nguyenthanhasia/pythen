"""Core RuleTreeEvaluator for PYTHEN framework (v1-compatible smoke fixture)."""
from typing import List, Dict, Any, Tuple, Optional
from .utils import log_message, validate_rules


class RuleTreeEvaluator:
    """Evaluates defeasible legal rule trees against lists of positive facts."""
    def __init__(self, rule_tree: List[Dict[str, Any]], enable_trace: bool = False):
        validate_rules(rule_tree)
        self.rule_tree = rule_tree
        self.node_map = {}
        self.enable_trace = enable_trace
        self.trace: List[Tuple[str, str, bool]] = []
        for node in rule_tree:
            if isinstance(node, dict) and 'p' in node and isinstance(node['p'], str):
                self.node_map[node['p']] = node
        log_message('INFO', f'RuleTreeEvaluator initialized with {len(self.node_map)} rules')

    def evaluate(self, facts: List[str], target_predicate: str) -> bool:
        self.trace = []
        try:
            result = self._eval_node(target_predicate, facts)
            log_message('INFO', f'Evaluation of "{target_predicate}" returned {result}')
            return result
        except Exception as e:
            log_message('ERROR', f'Evaluation error for "{target_predicate}": {str(e)}')
            return False

    def _eval_node(self, predicate: str, facts: List[str]) -> bool:
        if predicate not in self.node_map:
            is_fact = predicate in facts
            if self.enable_trace:
                self.trace.append((predicate, "FACT", is_fact))
            return is_fact
        node = self.node_map[predicate]
        conditions = node.get('conditions', [])
        exceptions = node.get('exceptions', [])
        operator = node.get('op', 'ALL')
        exceptions_met = any(self._eval_node(e, facts) for e in exceptions if isinstance(e, str))
        if exceptions_met:
            if self.enable_trace:
                self.trace.append((predicate, "EXCEPTION_MET", False))
            return False
        if operator in ['ALL', 'AND']:
            conditions_met = all(self._eval_node(c, facts) for c in conditions if isinstance(c, str))
            op_type = "ALL"
        elif operator in ['ANY', 'OR']:
            conditions_met = any(self._eval_node(c, facts) for c in conditions if isinstance(c, str))
            op_type = "ANY"
        else:
            log_message('WARNING', f'Unknown operator: {operator}')
            conditions_met = False
            op_type = "UNKNOWN"
        result = conditions_met and not exceptions_met
        if self.enable_trace:
            self.trace.append((predicate, op_type, result))
        return result

    def challenge(self, facts, target_predicate, candidates=None, max_changes=None):
        """Minimum-cardinality add-only challenge; see PYTHEN v2 framework."""
        from .reasoner import Reasoner
        return Reasoner(self.rule_tree, facts).challenge(
            target_predicate, candidates=candidates, max_changes=max_changes,
        )

    def get_trace(self) -> List[Tuple[str, str, bool]]:
        return self.trace

    def explain(self, facts: List[str], target_predicate: str) -> str:
        old_trace_setting = self.enable_trace
        self.enable_trace = True
        result = self.evaluate(facts, target_predicate)
        explanation = f"Evaluation of '{target_predicate}':\n"
        explanation += f"Result: {result}\n"
        explanation += f"Facts: {', '.join(facts)}\n\n"
        explanation += "Evaluation steps:\n"
        for i, (pred, eval_type, res) in enumerate(self.trace, 1):
            explanation += f"  {i}. {pred} ({eval_type}): {res}\n"
        self.enable_trace = old_trace_setting
        return explanation

    def get_applicable_rules(self, target_predicate: str) -> Optional[Dict[str, Any]]:
        return self.node_map.get(target_predicate)

    def get_all_predicates(self) -> List[str]:
        return list(self.node_map.keys())
