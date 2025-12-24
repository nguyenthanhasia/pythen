"""
PYTHEN Examples

This package contains end-to-end examples demonstrating PYTHEN's application
to various legal domains:

- gdpr_article17: GDPR Article 17 - Right to Erasure
- contract_law: Contract Law - Voidable Contracts

Each example includes realistic scenarios and demonstrates how to:
1. Define legal rules with conditions and exceptions
2. Evaluate rules against facts
3. Trace and explain evaluation results
"""

from . import gdpr_article17
from . import contract_law

__all__ = ["gdpr_article17", "contract_law"]
