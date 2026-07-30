"""Typed public data contracts for reliability scenarios and results."""

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path


type JsonScalar = str | int | float | bool | None
type JsonValue = JsonScalar | list[JsonValue] | dict[str, JsonValue]


class FaultKind(StrEnum):
    """Supported fault categories."""

    SANDBOX_RESTART = "sandbox_restart"
    LOST_DISPATCH_RESPONSE = "lost_dispatch_response"
    SIGKILL_MID_TOOL_CALL = "sigkill_mid_tool_call"
    NETWORK_PARTITION = "network_partition"


@dataclass(frozen=True, slots=True)
class EventTrigger:
    """Select a deterministic persisted-event occurrence."""

    event_type: str
    ordinal: int
    tool_call_id: str | None = None


@dataclass(frozen=True, slots=True)
class FaultSpec:
    """One compiled fault in a scenario schedule."""

    fault_id: str
    kind: FaultKind
    trigger: EventTrigger
    parameters: dict[str, JsonValue]


@dataclass(frozen=True, slots=True)
class Scenario:
    """Versioned, declarative benchmark scenario."""

    schema_version: int
    scenario_id: str
    benchmark: str
    instance_id: str
    agent_config: str
    seed: int
    faults: tuple[FaultSpec, ...]


@dataclass(frozen=True, slots=True)
class RunIdentity:
    """Stable identity and artifact root for one scenario run."""

    run_id: str
    scenario_id: str
    seed: int
    artifact_dir: Path


@dataclass(frozen=True, slots=True)
class FaultReceipt:
    """Inspectable evidence that a scheduled fault was applied."""

    run_id: str
    fault_id: str
    kind: FaultKind
    monotonic_seconds: float
    event_id: str | None
    tool_call_id: str | None
    details: dict[str, JsonValue]


@dataclass(frozen=True, slots=True)
class GraderResult:
    """One inspectable grader result."""

    grader: str
    passed: bool
    value: float | int | bool | None
    reason_codes: tuple[str, ...]
    evidence_refs: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ReliabilityResult:
    """Combined task and reliability outcome for one run."""

    run: RunIdentity
    task_passed: bool
    completion_resume: GraderResult
    no_duplicate_effect: GraderResult
    recovery_overhead: GraderResult
