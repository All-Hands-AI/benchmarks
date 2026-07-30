"""Inspectable reliability grader contracts and empty entrypoints."""

from dataclasses import dataclass
from pathlib import Path

from benchmarks.reliability.models import GraderResult, JsonValue, Scenario


@dataclass(frozen=True, slots=True)
class GradingEvidence:
    """Artifact references supplied to deterministic graders."""

    scenario: Scenario
    task_result: dict[str, JsonValue]
    events_path: Path
    fault_receipts_path: Path
    recovery_receipts_path: Path
    effects_path: Path
    metrics_path: Path
    baseline_metrics_path: Path | None


def grade_completion_resume(evidence: GradingEvidence) -> GraderResult:
    """Judge task completion and genuine resume from explicit receipts."""
    # TODO: implement stable reason codes and evidence references.
    raise NotImplementedError


def grade_no_duplicate_effect(evidence: GradingEvidence) -> GraderResult:
    """Judge committed effect counts using the scenario-owned ledger."""
    # TODO: compare intended logical operations with committed effects.
    raise NotImplementedError


def grade_recovery_overhead(evidence: GradingEvidence) -> GraderResult:
    """Compare faulted metrics with the matched no-fault baseline."""
    # TODO: report raw deltas/ratios and explicit missing-baseline results.
    raise NotImplementedError
