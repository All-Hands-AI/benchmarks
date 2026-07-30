"""Deterministic schedule compilation and trigger matching stubs."""

from collections.abc import Iterable
from typing import Protocol

from benchmarks.reliability.models import FaultSpec, Scenario


class EventView(Protocol):
    """Minimal persisted-event view used by the scheduler."""

    @property
    def id(self) -> str:
        """Return the stable event ID."""
        ...

    @property
    def event_type(self) -> str:
        """Return the serialized event type."""
        ...


class FaultSchedule:
    """Compiled deterministic schedule for one scenario."""

    def __init__(self, scenario: Scenario) -> None:
        """Create an unimplemented schedule from a resolved scenario."""
        # TODO: compile ordered triggers with a scenario-local RNG.
        raise NotImplementedError

    def pending(self) -> tuple[FaultSpec, ...]:
        """Return faults that have not fired."""
        # TODO: return immutable pending schedule state.
        raise NotImplementedError

    def observe(self, events: Iterable[EventView]) -> tuple[FaultSpec, ...]:
        """Return faults whose deterministic triggers match new events."""
        # TODO: match persisted event identities and ordinals.
        raise NotImplementedError


def compile_schedule(scenario: Scenario) -> FaultSchedule:
    """Compile a scenario into a deterministic fault schedule."""
    # TODO: validate schedule determinism and instantiate FaultSchedule.
    raise NotImplementedError
