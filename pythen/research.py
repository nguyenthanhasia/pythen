"""Lightweight, deterministic research artifacts for independent paper workflows.

No LLM/agent SDK is part of PYTHEN's reasoning core.
"""
import json
from pathlib import Path
from typing import Any

from .analysis import AnalysisResult
from .intervention import EvidenceState
from .graph import RuleGraph


def experiment_record(graph: RuleGraph, evidence: EvidenceState, result: AnalysisResult) -> dict:
    """JSON-safe provenance and exact/query-budget guarantee metadata."""
    return {
        "schema_version": 1,
        "framework": "pythen-v2",
        "graph_sha256": graph.fingerprint,
        "rules": list(graph.to_rules()),
        "facts": sorted(evidence.facts),
        "analysis": {
            "method": result.method,
            "target": result.target,
            "original_verdict": result.original_verdict,
            "status": result.status,
            "radius": result.radius,
            "witness": list(result.witness),
            "candidates": list(result.candidates),
            "evaluations": result.evaluations,
            "searched_up_to": result.searched_up_to,
            "guarantee": result.guarantee,
            "metadata": dict(result.metadata),
        },
    }


def export_experiment(path, graph: RuleGraph, evidence: EvidenceState,
                      result: AnalysisResult):
    """Write reproducible JSON for later benchmarking, plots, or papers."""
    data = experiment_record(graph, evidence, result)
    Path(path).write_text(json.dumps(data, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return data


