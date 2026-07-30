"""Runner-level orchestration signatures for a future Evaluation subclass."""

from collections.abc import Callable
from typing import Protocol

from benchmarks.reliability.models import ReliabilityResult, Scenario


class ResultSink(Protocol):
    """Persist one completed reliability result."""

    def __call__(self, result: ReliabilityResult) -> None:
        """Write one result without mutating it."""
        ...


def run_scenario(
    scenario: Scenario,
    *,
    on_result: ResultSink | Callable[[ReliabilityResult], None],
) -> ReliabilityResult:
    """Run one real benchmark scenario under its fault schedule."""
    # TODO: integrate with Evaluation._execute_single_attempt after approval.
    raise NotImplementedError


def run_baseline(scenario: Scenario) -> ReliabilityResult:
    """Run the matched scenario without injecting scheduled faults."""
    # TODO: preserve all non-fault configuration and source identities.
    raise NotImplementedError
