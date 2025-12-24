"""
Contract Law Example - Voidable Contracts

This example demonstrates PYTHEN's application to contract law,
specifically determining when a contract is voidable.

This shows how PYTHEN can model complex legal doctrines with
multiple conditions and exceptions.
"""

from pythen import RuleTreeEvaluator, print_rules


# Define the rule set for voidable contracts
VOIDABLE_CONTRACT_RULES = [
    {
        "p": "contract_voidable",
        "op": "ANY",
        "conditions": [
            "party_lacks_capacity",
            "contract_induced_by_fraud",
            "contract_induced_by_duress",
            "contract_induced_by_undue_influence",
            "contract_induced_by_misrepresentation"
        ],
        "exceptions": [
            "contract_for_necessities",
            "contract_ratified",
            "contract_performed",
            "party_waived_right"
        ]
    },
    {
        "p": "party_lacks_capacity",
        "op": "ANY",
        "conditions": [
            "party_is_minor",
            "party_is_mentally_incapacitated",
            "party_is_intoxicated"
        ],
        "exceptions": []
    },
    {
        "p": "party_is_minor",
        "op": "ALL",
        "conditions": ["party_age_below_18"],
        "exceptions": []
    },
    {
        "p": "party_is_mentally_incapacitated",
        "op": "ALL",
        "conditions": ["party_lacks_mental_capacity"],
        "exceptions": []
    },
    {
        "p": "contract_induced_by_fraud",
        "op": "ALL",
        "conditions": [
            "false_statement_made",
            "statement_material",
            "party_relied_on_statement",
            "party_suffered_damage"
        ],
        "exceptions": []
    },
    {
        "p": "contract_induced_by_duress",
        "op": "ALL",
        "conditions": [
            "threat_made",
            "threat_unlawful",
            "threat_induced_contract"
        ],
        "exceptions": []
    },
    {
        "p": "contract_induced_by_undue_influence",
        "op": "ALL",
        "conditions": [
            "relationship_of_trust",
            "excessive_pressure_applied",
            "party_did_not_act_freely"
        ],
        "exceptions": []
    },
    {
        "p": "contract_induced_by_misrepresentation",
        "op": "ALL",
        "conditions": [
            "false_representation_made",
            "representation_material",
            "party_relied_on_representation"
        ],
        "exceptions": []
    },
    {
        "p": "contract_for_necessities",
        "op": "ALL",
        "conditions": ["goods_are_necessities"],
        "exceptions": []
    }
]


def example_1_minor_contract():
    """
    Example 1: Contract with a minor
    
    Scenario: A 16-year-old purchases a video game console.
    The contract is voidable because the party is a minor.
    However, if the goods are necessities, the contract may be enforceable.
    """
    print("\n" + "="*70)
    print("EXAMPLE 1: Contract with a Minor")
    print("="*70)
    
    print("\nScenario A: Non-necessity goods (video game console)")
    facts_a = ["party_age_below_18"]
    
    evaluator = RuleTreeEvaluator(VOIDABLE_CONTRACT_RULES, enable_trace=True)
    result_a = evaluator.evaluate(facts_a, "contract_voidable")
    
    print(f"Facts: {facts_a}")
    print(f"Is contract voidable? {result_a}")
    
    print("\n" + "-"*70)
    print("\nScenario B: Necessity goods (food, clothing)")
    facts_b = ["party_age_below_18", "goods_are_necessities"]
    
    result_b = evaluator.evaluate(facts_b, "contract_voidable")
    
    print(f"Facts: {facts_b}")
    print(f"Is contract voidable? {result_b}")
    print("\nExplanation:")
    print(evaluator.explain(facts_b, "contract_voidable"))


def example_2_fraud():
    """
    Example 2: Contract induced by fraud
    
    Scenario: A seller misrepresents the condition of a car.
    The buyer discovers the fraud and seeks to void the contract.
    """
    print("\n" + "="*70)
    print("EXAMPLE 2: Contract Induced by Fraud")
    print("="*70)
    
    facts = [
        "false_statement_made",
        "statement_material",
        "party_relied_on_statement",
        "party_suffered_damage"
    ]
    
    evaluator = RuleTreeEvaluator(VOIDABLE_CONTRACT_RULES, enable_trace=True)
    result = evaluator.evaluate(facts, "contract_voidable")
    
    print(f"\nFacts: {facts}")
    print(f"Is contract voidable? {result}")
    print("\nExplanation:")
    print(evaluator.explain(facts, "contract_voidable"))


def example_3_duress():
    """
    Example 3: Contract induced by duress
    
    Scenario: A person is threatened with violence unless they sign a contract.
    The contract is voidable due to duress.
    """
    print("\n" + "="*70)
    print("EXAMPLE 3: Contract Induced by Duress")
    print("="*70)
    
    facts = [
        "threat_made",
        "threat_unlawful",
        "threat_induced_contract"
    ]
    
    evaluator = RuleTreeEvaluator(VOIDABLE_CONTRACT_RULES, enable_trace=True)
    result = evaluator.evaluate(facts, "contract_voidable")
    
    print(f"\nFacts: {facts}")
    print(f"Is contract voidable? {result}")
    print("\nExplanation:")
    print(evaluator.explain(facts, "contract_voidable"))


def example_4_ratification():
    """
    Example 4: Contract with ratification
    
    Scenario: A minor enters into a contract, but later ratifies it
    (affirms it after reaching majority). The contract is no longer voidable.
    """
    print("\n" + "="*70)
    print("EXAMPLE 4: Contract Ratification")
    print("="*70)
    
    facts = [
        "party_age_below_18",
        "contract_ratified"  # Exception: contract has been ratified
    ]
    
    evaluator = RuleTreeEvaluator(VOIDABLE_CONTRACT_RULES, enable_trace=True)
    result = evaluator.evaluate(facts, "contract_voidable")
    
    print(f"\nFacts: {facts}")
    print(f"Is contract voidable? {result}")
    print("\nExplanation:")
    print(evaluator.explain(facts, "contract_voidable"))


def example_5_mental_incapacity():
    """
    Example 5: Contract with mentally incapacitated party
    
    Scenario: A person with dementia signs a contract.
    The contract is voidable due to lack of mental capacity.
    """
    print("\n" + "="*70)
    print("EXAMPLE 5: Mental Incapacity")
    print("="*70)
    
    facts = [
        "party_lacks_mental_capacity"
    ]
    
    evaluator = RuleTreeEvaluator(VOIDABLE_CONTRACT_RULES, enable_trace=True)
    result = evaluator.evaluate(facts, "contract_voidable")
    
    print(f"\nFacts: {facts}")
    print(f"Is contract voidable? {result}")
    print("\nExplanation:")
    print(evaluator.explain(facts, "contract_voidable"))


def main():
    """Run all examples."""
    print("\n" + "="*70)
    print("PYTHEN: Contract Law - Voidable Contracts Examples")
    print("="*70)
    
    # Print the rule set
    print_rules(VOIDABLE_CONTRACT_RULES)
    
    # Run examples
    example_1_minor_contract()
    example_2_fraud()
    example_3_duress()
    example_4_ratification()
    example_5_mental_incapacity()
    
    print("\n" + "="*70)
    print("Examples completed!")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
