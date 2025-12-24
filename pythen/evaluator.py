"""
Core RuleTreeEvaluator for PYTHEN framework.

This module provides the main evaluation engine for legal reasoning with defeasible rules.
"""

from typing import List, Dict, Any, Tuple, Optional
from .utils import log_message, validate_rules


class RuleTreeEvaluator:
    """
    Evaluates a tree of legal rules against a set of facts.
    
    The evaluator supports defeasible reasoning with explicit exception handling.
    Rules can use either conjunctive (ALL) or disjunctive (ANY) conditions.
    
    Attributes:
        rule_tree (List[Dict]): List of rule dictionaries
        node_map (Dict[str, Dict]): Mapping of proposition names to rule definitions
        trace (List[Tuple]): Trace of evaluation steps for debugging
    """
    
    def __init__(self, rule_tree: List[Dict[str, Any]], enable_trace: bool = False):
        """
        Initialize the RuleTreeEvaluator.
        
        Args:
            rule_tree: List of rule dictionaries with keys 'p', 'op', 'conditions', 'exceptions'
            enable_trace: If True, enables detailed tracing of evaluation steps
            
        Raises:
            ValueError: If rule_tree is invalid
        """
        # Validate rules before initialization
        validate_rules(rule_tree)
        
        self.rule_tree = rule_tree
        self.node_map = {}
        self.enable_trace = enable_trace
        self.trace: List[Tuple[str, str, bool]] = []
        
        # Build node map for O(1) lookup
        for node in rule_tree:
            if isinstance(node, dict) and 'p' in node and isinstance(node['p'], str):
                self.node_map[node['p']] = node
        
        log_message('INFO', f'RuleTreeEvaluator initialized with {len(self.node_map)} rules')

    def evaluate(self, facts: List[str], target_predicate: str) -> bool:
        """
        Evaluate whether a target predicate is true given a set of facts.
        
        Args:
            facts: List of fact strings that are considered true
            target_predicate: The predicate to evaluate
            
        Returns:
            bool: True if the target predicate is satisfied, False otherwise
            
        Example:
            >>> rules = [{
            ...     "p": "contract_voidable",
            ...     "op": "ANY",
            ...     "conditions": ["is_minor", "is_incapacitated"],
            ...     "exceptions": ["for_necessities"]
            ... }]
            >>> evaluator = RuleTreeEvaluator(rules)
            >>> facts = ["is_minor"]
            >>> result = evaluator.evaluate(facts, "contract_voidable")
            >>> print(result)  # True
        """
        self.trace = []
        try:
            result = self._eval_node(target_predicate, facts)
            log_message('INFO', f'Evaluation of "{target_predicate}" returned {result}')
            return result
        except Exception as e:
            log_message('ERROR', f'Evaluation error for "{target_predicate}": {str(e)}')
            return False

    def _eval_node(self, predicate: str, facts: List[str]) -> bool:
        """
        Recursively evaluate a predicate node.
        
        Args:
            predicate: The predicate to evaluate
            facts: List of known facts
            
        Returns:
            bool: True if the predicate is satisfied, False otherwise
        """
        # Base case: predicate is a fact
        if predicate not in self.node_map:
            is_fact = predicate in facts
            if self.enable_trace:
                self.trace.append((predicate, "FACT", is_fact))
            return is_fact
        
        # Get the rule definition
        node = self.node_map[predicate]
        conditions = node.get('conditions', [])
        exceptions = node.get('exceptions', [])
        operator = node.get('op', 'ALL')
        
        # Evaluate exceptions first (exception-first approach)
        exceptions_met = any(
            self._eval_node(e, facts) 
            for e in exceptions 
            if isinstance(e, str)
        )
        
        if exceptions_met:
            if self.enable_trace:
                self.trace.append((predicate, "EXCEPTION_MET", False))
            return False
        
        # Evaluate conditions based on operator
        if operator in ['ALL', 'AND']:
            conditions_met = all(
                self._eval_node(c, facts) 
                for c in conditions 
                if isinstance(c, str)
            )
            op_type = "ALL"
        elif operator in ['ANY', 'OR']:
            conditions_met = any(
                self._eval_node(c, facts) 
                for c in conditions 
                if isinstance(c, str)
            )
            op_type = "ANY"
        else:
            log_message('WARNING', f'Unknown operator: {operator}')
            conditions_met = False
            op_type = "UNKNOWN"
        
        result = conditions_met and not exceptions_met
        
        if self.enable_trace:
            self.trace.append((predicate, f"{op_type}", result))
        
        return result

    def get_trace(self) -> List[Tuple[str, str, bool]]:
        """
        Get the evaluation trace (only available if enable_trace=True).
        
        Returns:
            List of tuples: (predicate, evaluation_type, result)
        """
        return self.trace

    def explain(self, facts: List[str], target_predicate: str) -> str:
        """
        Generate a human-readable explanation of the evaluation.
        
        Args:
            facts: List of known facts
            target_predicate: The predicate to evaluate
            
        Returns:
            str: Human-readable explanation
        """
        # Enable tracing for explanation
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
        """
        Get the rule definition for a predicate.
        
        Args:
            target_predicate: The predicate to look up
            
        Returns:
            Dict with rule definition, or None if not found
        """
        return self.node_map.get(target_predicate)

    def get_all_predicates(self) -> List[str]:
        """
        Get all predicates defined in the rule tree.
        
        Returns:
            List of all predicate names
        """
        return list(self.node_map.keys())
