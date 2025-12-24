# Getting Started with PYTHEN

Welcome to the PYTHEN tutorial! This guide will walk you through the process of creating and evaluating a legal rule set from scratch.

## 1. What is a Rule?

In PYTHEN, a rule is a simple JSON object (a Python dictionary) that defines a legal proposition. It has four key components:

- `"p"`: The **proposition** you are defining (e.g., `"contract_is_valid"`).
- `"op"`: The **operator** to evaluate the conditions. It can be `"ALL"` (all conditions must be true) or `"ANY"` (at least one condition must be true).
- `"conditions"`: A list of other propositions that must be met.
- `"exceptions"`: A list of propositions that can defeat the rule, even if the conditions are met.

Here is a simple example:

```json
{
    "p": "can_vote",
    "op": "ALL",
    "conditions": ["is_citizen", "is_over_18"],
    "exceptions": ["is_disqualified"]
}
```

This rule states: "A person can vote if they are a citizen AND are over 18, UNLESS they are disqualified."

## 2. Creating a Rule Set

A rule set is simply a Python list of these rule dictionaries.

Let's create a rule set for our voting example:

```python
# voting_rules.py

VOTING_RULES = [
    {
        "p": "can_vote",
        "op": "ALL",
        "conditions": ["is_citizen", "is_over_18"],
        "exceptions": ["is_disqualified"]
    },
    {
        "p": "is_over_18",
        "op": "ALL",
        "conditions": ["age_is_18_or_more"],
        "exceptions": []
    },
    {
        "p": "is_disqualified",
        "op": "ANY",
        "conditions": ["has_felony_conviction", "is_mentally_incompetent"],
        "exceptions": []
    }
]
```

Notice how rules can refer to each other. The `can_vote` rule depends on `is_over_18` and `is_disqualified`, which are themselves defined by other rules.

## 3. Defining Facts for a Case

Facts are the specific details of a case. In PYTHEN, facts are represented as a simple list of strings.

Let's define the facts for two different people:

```python
# Case 1: Alice, a 25-year-old citizen
facts_alice = ["is_citizen", "age_is_18_or_more"]

# Case 2: Bob, a 30-year-old citizen with a felony conviction
facts_bob = ["is_citizen", "age_is_18_or_more", "has_felony_conviction"]
```

## 4. Evaluating a Case

Now, let's use the `RuleTreeEvaluator` to see if Alice and Bob can vote.

```python
from pythen import RuleTreeEvaluator
from voting_rules import VOTING_RULES

# Initialize the evaluator with our rule set
evaluator = RuleTreeEvaluator(VOTING_RULES)

# --- Evaluate Alice's case ---
can_alice_vote = evaluator.evaluate(facts_alice, "can_vote")
print(f"Can Alice vote? {can_alice_vote}")
# Output: Can Alice vote? True

# --- Evaluate Bob's case ---
can_bob_vote = evaluator.evaluate(facts_bob, "can_vote")
print(f"Can Bob vote? {can_bob_vote}")
# Output: Can Bob vote? False
```

### Why did Bob's evaluation return `False`?

Because the `is_disqualified` exception was met. The `has_felony_conviction` fact triggered the `is_disqualified` rule, which in turn defeated the `can_vote` rule.

## 5. Explaining the Reasoning

PYTHEN can provide a step-by-step explanation of its reasoning. This is crucial for transparency and debugging.

To get an explanation, simply call the `explain()` method.

```python
# Let's get an explanation for Bob's case
explanation = evaluator.explain(facts_bob, "can_vote")
print("\n--- Explanation for Bob's Case ---")
print(explanation)
```

This will produce a detailed trace of the evaluation, showing how each rule was evaluated and why the final conclusion was reached.

```
--- Explanation for Bob's Case ---
Evaluation of 'can_vote':
Result: False
Facts: is_citizen, age_is_18_or_more, has_felony_conviction

Evaluation steps:
  1. is_disqualified (EXCEPTION_MET): False
  2. can_vote (ALL): False
```

## Next Steps

You now have the basic knowledge to start building your own legal reasoning models with PYTHEN!

- Explore the more complex examples in the `examples/` directory.
- Read the **[API Reference](./api_reference.md)** for more advanced features.
- Check out the **[Rule Syntax](./rule_syntax.md)** guide for a complete overview of the rule format.
