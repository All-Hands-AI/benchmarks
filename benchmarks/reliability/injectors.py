"""Fault injection contracts; concrete injectors are intentionally absent."""

from typing import Protocol

from benchmarks.reliability.models import (
    FaultReceipt,
    FaultSpec,
    JsonValue,
    RunIdentity,
)


class FaultHandle(Protocol):
    """Opaque, injector-owned armed-fault handle."""

    @property
    def fault_id(self) -> str:
        """Return the corresponding fault ID."""
        ...


class FaultContext(Protocol):
    """Explicit runtime capabilities available to a fault injector."""

    @property
    def run(self) -> RunIdentity:
        """Return the current run identity."""
        ...

    def record(self, kind: str, details: dict[str, JsonValue]) -> None:
        """Persist an inspectable lifecycle or injection receipt."""
        ...


class FaultInjector(Protocol):
    """Arm, inject, and release one supported fault kind."""

    def arm(self, context: FaultContext, fault: FaultSpec) -> FaultHandle:
        """Prepare a fault without changing the target yet."""
        ...

    def inject(
        self,
        context: FaultContext,
        fault: FaultSpec,
        handle: FaultHandle,
    ) -> FaultReceipt:
        """Apply the fault and return an inspectable receipt."""
        ...

    def release(
        self,
        context: FaultContext,
        fault: FaultSpec,
        handle: FaultHandle,
    ) -> FaultReceipt | None:
        """Release a bounded fault, if the fault requires release."""
        ...


def injector_for(fault: FaultSpec) -> FaultInjector:
    """Resolve the injector registered for a fault specification."""
    # TODO: add explicit dependency injection after scope approval.
    raise NotImplementedError
