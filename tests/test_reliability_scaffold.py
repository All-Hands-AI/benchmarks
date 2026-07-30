"""Test skeleton for the reliability benchmark.

Feature tests remain skipped until maintainers confirm repository and scope.
"""

import pytest


@pytest.mark.skip(reason="phase 1 scaffold only; no feature logic authorized")
def test_schedule_is_deterministic_for_a_fixed_seed() -> None:
    """A compiled schedule should be stable for the same scenario and seed."""


@pytest.mark.skip(reason="phase 1 scaffold only; no feature logic authorized")
def test_duplicate_effect_grader_uses_external_ledger() -> None:
    """Duplicate-effect grading should not infer commits from agent events."""


@pytest.mark.skip(reason="phase 1 scaffold only; no feature logic authorized")
def test_fresh_retry_does_not_count_as_resume() -> None:
    """A new workspace/attempt should not satisfy the resume grader."""
