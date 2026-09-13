# PYTHEN: A Flexible Framework for Legal Reasoning in Python

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/python-3.7%2B-blue.svg)](https://www.python.org/)

**PYTHEN** is a Python-native framework for defeasible legal reasoning. It provides an intuitive, human-readable way to model complex legal rules, conditions, and exceptions, making formal legal reasoning accessible to developers, legal professionals, and researchers without extensive logic programming expertise.

Inspired by **PROLEG** (PROlog-based LEGal reasoning support system) and guided by the philosophy of **The Zen of Python**, PYTHEN bridges the gap between powerful symbolic reasoning systems and the practical, ubiquitous Python ecosystem.

## Key Features

- **Simple & Readable Syntax**: Rules are defined in a clean JSON format that is easy to read and write.
- **Python-Native Philosophy**: The design is inspired by The Zen of Python, emphasizing simplicity, readability, and practicality. The `ALL` and `ANY` operators directly mirror Python's built-in `all()` and `any()` functions.
- **Defeasible Reasoning**: Explicitly model exceptions to rules, a core feature of legal reasoning.
- **Accessible**: Designed for developers, legal scholars, and students who are comfortable with Python but may not be experts in Prolog or formal logic.
- **LLM-Friendly**: The structured JSON format makes PYTHEN an ideal target for autoformalization pipelines, where Large Language Models (LLMs) translate natural language legal text into executable rules.
- **Explainable AI (XAI)**: Generate clear, step-by-step explanations of the reasoning process for transparency and debugging.
- **Zero Dependencies**: The core evaluator is written in pure Python with no external dependencies.

## Philosophy: The Zen of Python in Legal Tech

PYTHEN's design is deeply influenced by The Zen of Python (PEP 20). We believe these principles are especially relevant for legal technology:

> - **Beautiful is better than ugly.** Legal rules should be represented cleanly.
> - **Explicit is better than implicit.** Exceptions and conditions are stated clearly in each rule.
> - **Simple is better than complex.** No need to learn a complex new syntax if you already know Python and JSON.
> - **Readability counts.** A legal rule base should be understandable by lawyers, not just programmers.

By adhering to these principles, PYTHEN aims to make computational law more accessible, transparent, and maintainable.

## Installation

**From PyPI (Recommended):**

```bash
pip install pythen
```

**For Development:**

```bash
git clone https://github.com/nguyenthanhasia/pythen.git
cd pythen
pip install -e .
```

## Quickstart: 30-Second Example

Let's model a simple rule: "A contract is voidable if the party was a minor, UNLESS the contract was for necessities."

**1. Define the Rules**

Create a list of rule dictionaries. The `op` can be `ANY` (like Python's `any()`) or `ALL` (like `all()`).

```python
from pythen import RuleTreeEvaluator

# Define the rule set
contract_rules = [
    {
        "p": "contract_voidable",
        "op": "ANY",
        "conditions": ["party_is_minor"],
        "exceptions": ["contract_for_necessities"]
    },
    {
        "p": "party_is_minor",
        "op": "ALL",
        "conditions": ["party_age_below_18"],
        "exceptions": []
    }
]
```

**2. Define the Facts**

Create a list of facts for a specific case.

```python
# Case 1: A 16-year-old buys a luxury item
facts_case_1 = ["party_age_below_18"]

# Case 2: A 17-year-old buys food (a necessity)
facts_case_2 = ["party_age_below_18", "contract_for_necessities"]
```

**3. Evaluate**

Instantiate the `RuleTreeEvaluator` and evaluate the target predicate against the facts.

```python
evaluator = RuleTreeEvaluator(contract_rules)

# Evaluate Case 1
result_1 = evaluator.evaluate(facts_case_1, "contract_voidable")
print(f"Case 1 (Luxury Item): Is contract voidable? {result_1}")
# Output: Case 1 (Luxury Item): Is contract voidable? True

# Evaluate Case 2
result_2 = evaluator.evaluate(facts_case_2, "contract_voidable")
print(f"Case 2 (Necessities): Is contract voidable? {result_2}")
# Output: Case 2 (Necessities): Is contract voidable? False
```

## Documentation

For more detailed information, please see the `docs` directory:

- **[Getting Started](./docs/getting_started.md)**: A full tutorial on using PYTHEN.
- **[API Reference](./docs/api_reference.md)**: Detailed documentation for the `RuleTreeEvaluator` class and utility functions.
- **[Rule Syntax](./docs/rule_syntax.md)**: A complete guide to the JSON rule format.
- **[Philosophy](./docs/philosophy.md)**: A deeper dive into the design principles behind PYTHEN.

## Examples

This repository includes several end-to-end examples in the `examples/` directory:

- **[GDPR Article 17 (Right to Erasure)](./examples/gdpr_article17.py)**: A comprehensive model of the "Right to be Forgotten," demonstrating how to handle multiple conditions and exceptions in a real-world regulation.
- **[Contract Law (Voidable Contracts)](./examples/contract_law.py)**: A model of the conditions that make a contract voidable, such as lack of capacity or duress.

To run the examples:

```bash
python3 examples/gdpr_article17.py
python3 examples/contract_law.py
```

## Contributing

Contributions are welcome! Whether you're a developer, a legal scholar, or a student, you can help improve PYTHEN. Please see our [Contributing Guidelines](./CONTRIBUTING.md) for more details on how to get started.

## License

PYTHEN is licensed under the [MIT License](./LICENSE).

## Citing PYTHEN

If you use PYTHEN in your research, please cite our work.

```bibtex
@inproceedings{nguyen2026pythen,
  title     = {PYTHEN: A Flexible Framework for Legal Reasoning in Python},
  author    = {Nguyen, Ha-Thanh and Satoh, Ken},
  booktitle = {Local Proceedings of the 20th International Workshop on Juris-Informatics (JURISIN 2026)},
  pages     = {17--30},
  year      = {2026},
  isbn      = {978-4-915905-98-8}
}
```

