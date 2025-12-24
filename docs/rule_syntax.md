# PYTHEN Rule Syntax

PYTHEN uses a simple and expressive JSON-based syntax for defining legal rules. This guide provides a complete overview of the rule format.

## The Rule Object

A rule is a JSON object (a Python dictionary) with four main fields: `p`, `op`, `conditions`, and `exceptions`.

```json
{
    "p": "proposition_name",
    "op": "OPERATOR",
    "conditions": ["condition1", "condition2"],
    "exceptions": ["exception1"]
}
```

### `p`: Proposition

- **Type**: `String`
- **Required**: Yes

This is the name of the legal proposition that the rule defines. It must be a unique string within the rule set.

### `op`: Operator

- **Type**: `String`
- **Required**: Yes
- **Values**: `"ALL"` (or `"AND"`), `"ANY"` (or `"OR"`)

This operator determines how the `conditions` are evaluated:

- `"ALL"`: All propositions in the `conditions` list must be true. This is equivalent to a logical **AND** and mirrors Python's `all()` function.
- `"ANY"`: At least one proposition in the `conditions` list must be true. This is equivalent to a logical **OR** and mirrors Python's `any()` function.

### `conditions`: Conditions

- **Type**: `List[String]`
- **Required**: Yes

This is a list of strings, where each string is the name of another proposition. These are the requirements that must be met for the main proposition `p` to be considered true (before checking for exceptions).

### `exceptions`: Exceptions

- **Type**: `List[String]`
- **Required**: No (defaults to an empty list `[]`)

This is a list of strings, where each string is the name of a proposition that can **defeat** the rule. If any of the propositions in the `exceptions` list are true, the main proposition `p` will be false, regardless of whether its conditions were met.

This is the core mechanism for modeling **defeasible reasoning**.

## Example: A Complete Rule Set

Let's look at a complete rule set for a simplified version of GDPR's "Right to Erasure."

```json
[
    {
        "p": "right_to_erasure_applies",
        "op": "ANY",
        "conditions": [
            "data_no_longer_necessary",
            "consent_withdrawn"
        ],
        "exceptions": [
            "needed_for_legal_claim",
            "needed_for_public_health"
        ]
    },
    {
        "p": "data_no_longer_necessary",
        "op": "ALL",
        "conditions": ["purpose_achieved"],
        "exceptions": []
    },
    {
        "p": "consent_withdrawn",
        "op": "ALL",
        "conditions": ["consent_was_basis", "user_revoked_consent"],
        "exceptions": []
    }
]
```

### How it Works:

1.  The main rule `right_to_erasure_applies` is true if `ANY` of its conditions are met (`data_no_longer_necessary` OR `consent_withdrawn`).
2.  However, it will be defeated if `ANY` of its exceptions are true (`needed_for_legal_claim` OR `needed_for_public_health`).
3.  The conditions themselves are defined by other rules. For example, `consent_withdrawn` is only true if `consent_was_basis` AND `user_revoked_consent` are both true.

This structure allows you to build complex, hierarchical models of legal reasoning in a way that remains readable and maintainable.
