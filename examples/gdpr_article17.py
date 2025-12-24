"""
GDPR Article 17 - Right to Erasure Example

This example demonstrates PYTHEN's application to GDPR Article 17 (Right to be Forgotten).
It shows how to model complex legal rules with conditions and exceptions.

Reference: https://gdpr-info.eu/art-17-gdpr/
"""

from pythen import RuleTreeEvaluator, print_rules


# Define the rule set for GDPR Article 17
GDPR_ARTICLE_17_RULES = [
    {
        "p": "art17_erasure_applicable",
        "op": "ANY",
        "conditions": [
            "no_longer_necessary",
            "consent_withdrawn",
            "object_to_processing",
            "processing_unlawful",
            "child_data_collected"
        ],
        "exceptions": [
            "freedom_of_expression",
            "legal_obligation",
            "public_interest_archiving_research",
            "legal_claims"
        ]
    },
    {
        "p": "no_longer_necessary",
        "op": "ALL",
        "conditions": ["data_not_needed_for_purpose"],
        "exceptions": []
    },
    {
        "p": "consent_withdrawn",
        "op": "ALL",
        "conditions": ["consent_was_basis", "consent_is_withdrawn"],
        "exceptions": []
    },
    {
        "p": "object_to_processing",
        "op": "ANY",
        "conditions": ["objection_no_overriding_grounds", "objection_to_direct_marketing"],
        "exceptions": []
    },
    {
        "p": "processing_unlawful",
        "op": "ALL",
        "conditions": ["processing_is_unlawful"],
        "exceptions": []
    },
    {
        "p": "child_data_collected",
        "op": "ALL",
        "conditions": ["data_collected_from_child"],
        "exceptions": []
    },
    {
        "p": "objection_no_overriding_grounds",
        "op": "ALL",
        "conditions": ["objection_made", "no_overriding_grounds"],
        "exceptions": []
    }
]


def example_1_consent_withdrawal():
    """
    Example 1: User withdraws consent for direct marketing
    
    Scenario: A user previously gave consent for marketing emails.
    They now withdraw that consent and request erasure.
    """
    print("\n" + "="*70)
    print("EXAMPLE 1: Consent Withdrawal for Direct Marketing")
    print("="*70)
    
    facts = [
        "consent_was_basis",
        "consent_is_withdrawn",
        "data_not_needed_for_purpose"
    ]
    
    evaluator = RuleTreeEvaluator(GDPR_ARTICLE_17_RULES, enable_trace=True)
    result = evaluator.evaluate(facts, "art17_erasure_applicable")
    
    print(f"\nFacts: {facts}")
    print(f"\nShould data be erased? {result}")
    print("\nExplanation:")
    print(evaluator.explain(facts, "art17_erasure_applicable"))


def example_2_with_exception():
    """
    Example 2: Legal obligation exception
    
    Scenario: User requests erasure, but data must be retained for legal claims.
    """
    print("\n" + "="*70)
    print("EXAMPLE 2: Legal Obligation Exception")
    print("="*70)
    
    facts = [
        "consent_was_basis",
        "consent_is_withdrawn",
        "legal_claims"  # Exception: legal claims pending
    ]
    
    evaluator = RuleTreeEvaluator(GDPR_ARTICLE_17_RULES, enable_trace=True)
    result = evaluator.evaluate(facts, "art17_erasure_applicable")
    
    print(f"\nFacts: {facts}")
    print(f"\nShould data be erased? {result}")
    print("\nExplanation:")
    print(evaluator.explain(facts, "art17_erasure_applicable"))


def example_3_child_data():
    """
    Example 3: Child data erasure
    
    Scenario: Data of a child was collected without proper consent.
    The child (or parent) requests erasure.
    """
    print("\n" + "="*70)
    print("EXAMPLE 3: Child Data Erasure")
    print("="*70)
    
    facts = [
        "data_collected_from_child"
    ]
    
    evaluator = RuleTreeEvaluator(GDPR_ARTICLE_17_RULES, enable_trace=True)
    result = evaluator.evaluate(facts, "art17_erasure_applicable")
    
    print(f"\nFacts: {facts}")
    print(f"\nShould data be erased? {result}")
    print("\nExplanation:")
    print(evaluator.explain(facts, "art17_erasure_applicable"))


def example_4_freedom_of_expression():
    """
    Example 4: Freedom of expression exception
    
    Scenario: User requests erasure, but data is needed for freedom of expression.
    """
    print("\n" + "="*70)
    print("EXAMPLE 4: Freedom of Expression Exception")
    print("="*70)
    
    facts = [
        "processing_is_unlawful",
        "freedom_of_expression"  # Exception: freedom of expression
    ]
    
    evaluator = RuleTreeEvaluator(GDPR_ARTICLE_17_RULES, enable_trace=True)
    result = evaluator.evaluate(facts, "art17_erasure_applicable")
    
    print(f"\nFacts: {facts}")
    print(f"\nShould data be erased? {result}")
    print("\nExplanation:")
    print(evaluator.explain(facts, "art17_erasure_applicable"))


def example_5_complex_scenario():
    """
    Example 5: Complex scenario with multiple conditions and exceptions
    
    Scenario: User objects to processing, but there are overriding grounds.
    """
    print("\n" + "="*70)
    print("EXAMPLE 5: Complex Scenario - Objection with Overriding Grounds")
    print("="*70)
    
    facts = [
        "objection_made",
        "no_overriding_grounds",  # Actually, there ARE overriding grounds
        "legal_obligation"  # Exception: legal obligation
    ]
    
    evaluator = RuleTreeEvaluator(GDPR_ARTICLE_17_RULES, enable_trace=True)
    result = evaluator.evaluate(facts, "art17_erasure_applicable")
    
    print(f"\nFacts: {facts}")
    print(f"\nShould data be erased? {result}")
    print("\nExplanation:")
    print(evaluator.explain(facts, "art17_erasure_applicable"))


def main():
    """Run all examples."""
    print("\n" + "="*70)
    print("PYTHEN: GDPR Article 17 - Right to Erasure Examples")
    print("="*70)
    
    # Print the rule set
    print_rules(GDPR_ARTICLE_17_RULES)
    
    # Run examples
    example_1_consent_withdrawal()
    example_2_with_exception()
    example_3_child_data()
    example_4_freedom_of_expression()
    example_5_complex_scenario()
    
    print("\n" + "="*70)
    print("Examples completed!")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
