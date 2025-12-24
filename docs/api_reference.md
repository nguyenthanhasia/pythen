# API Reference

This document provides a detailed API reference for the PYTHEN library.

## `RuleTreeEvaluator` Class

The `RuleTreeEvaluator` is the main class for evaluating legal rule sets.

### `__init__(self, rule_tree, enable_trace=False)`

Initializes the evaluator.

- **`rule_tree`** (`List[Dict]`): A list of rule dictionaries. The structure of these rules is validated upon initialization.
- **`enable_trace`** (`bool`, optional): If `True`, the evaluator will record a detailed trace of its reasoning steps. Defaults to `False`.

```python
from pythen import RuleTreeEvaluator

rules = [...] # Your list of rules
evaluator = RuleTreeEvaluator(rules, enable_trace=True)
```

### `evaluate(self, facts, target_predicate)`

Evaluates a target predicate against a set of facts.

- **`facts`** (`List[str]`): A list of strings representing the known facts for the case.
- **`target_predicate`** (`str`): The name of the proposition (`p`) you want to evaluate.

**Returns**: `bool` - `True` if the predicate is satisfied, `False` otherwise.

```python
facts = ["is_citizen", "age_is_18_or_more"]
result = evaluator.evaluate(facts, "can_vote")
```

### `explain(self, facts, target_predicate)`

Generates a human-readable explanation of the evaluation process.

This method automatically enables tracing for the evaluation to provide a step-by-step breakdown.

- **`facts`** (`List[str]`): The facts of the case.
- **`target_predicate`** (`str`): The predicate to explain.

**Returns**: `str` - A formatted string detailing the evaluation steps.

```python
explanation = evaluator.explain(facts, "can_vote")
print(explanation)
```

### `get_trace(self)`

Returns the evaluation trace if `enable_trace` was set to `True` during initialization.

**Returns**: `List[Tuple[str, str, bool]]` - A list of tuples, where each tuple represents a step in the evaluation: `(predicate, evaluation_type, result)`.

```python
trace = evaluator.get_trace()
for step in trace:
    print(f"Predicate: {step[0]}, Type: {step[1]}, Result: {step[2]}")
```

### `get_applicable_rules(self, target_predicate)`

Retrieves the rule definition for a specific predicate.

- **`target_predicate`** (`str`): The name of the predicate to look up.

**Returns**: `Dict` or `None` - The rule dictionary if found, otherwise `None`.

### `get_all_predicates(self)`

Returns a list of all predicates defined in the rule set.

**Returns**: `List[str]` - A list of all proposition names (`p`).

## Utility Functions

These functions are available in the `pythen.utils` module.

### `validate_rule(rule)`

Validates a single rule dictionary. Raises a `RuleValidationError` if the rule is invalid.

### `validate_rules(rules)`

Validates a list of rules. Raises a `RuleValidationError` if any rule is invalid or if there are duplicate proposition names.

### `load_rules_from_json(json_data)`

Loads and validates a rule set from a JSON string.

### `save_rules_to_json(rules)`

Converts a rule set into a formatted JSON string.

### `log_message(level, message)`

Logs a message using the built-in logger. Levels are `"DEBUG"`, `"INFO"`, `"WARNING"`, `"ERROR"`.

## Exceptions

### `RuleValidationError`

Custom exception raised by the validation functions when a rule or rule set does not conform to the required structure.
