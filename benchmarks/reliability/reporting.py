"""JSON/Markdown reliability scorecard signatures."""

from collections.abc import Iterable
from pathlib import Path

from benchmarks.reliability.models import ReliabilityResult


def write_scorecard_json(
    results: Iterable[ReliabilityResult],
    output_path: Path,
) -> None:
    """Write transparent aggregate metrics and per-run evidence links."""
    # TODO: serialize stable scorecard schema with raw numerators/denominators.
    raise NotImplementedError


def write_scorecard_markdown(
    results: Iterable[ReliabilityResult],
    output_path: Path,
) -> None:
    """Write a human-readable scorecard without hiding component scores."""
    # TODO: render grouped task, resume, duplicate, and overhead metrics.
    raise NotImplementedError
