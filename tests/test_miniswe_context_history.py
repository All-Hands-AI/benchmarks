from __future__ import annotations

import importlib.util
from pathlib import Path


_HISTORY_PATH = (
    Path(__file__).parents[1]
    / "extras/miniswe-context-model/src/openhands_miniswe_context_model/history.py"
)
_SPEC = importlib.util.spec_from_file_location("miniswe_context_history", _HISTORY_PATH)
assert _SPEC and _SPEC.loader
_HISTORY = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_HISTORY)
bound_message_history = _HISTORY.bound_message_history


def _turn(index: int, size: int = 80) -> list[dict]:
    return [
        {
            "role": "assistant",
            "content": f"turn-{index}",
            "tool_calls": [{"id": f"call-{index}", "function": {"name": "bash"}}],
        },
        {"role": "tool", "tool_call_id": f"call-{index}", "content": "x" * size},
    ]


def test_short_history_is_unchanged() -> None:
    messages = [
        {"role": "system", "content": "system"},
        {"role": "user", "content": "task"},
        *_turn(1),
    ]

    assert bound_message_history(messages, max_chars=10_000) == messages


def test_long_history_keeps_header_and_complete_recent_turns() -> None:
    messages = [
        {"role": "system", "content": "system"},
        {"role": "user", "content": "task"},
        *[message for index in range(12) for message in _turn(index, size=120)],
    ]

    bounded = bound_message_history(messages, max_chars=1_200, min_recent_units=3)

    assert bounded[:2] == messages[:2]
    assert "messages omitted" in bounded[2]["content"]
    assert bounded[-2:] == messages[-2:]
    for index, message in enumerate(bounded):
        if message["role"] == "tool":
            assert index > 0
            assert bounded[index - 1]["role"] in {"assistant", "tool"}


def test_history_budget_validation() -> None:
    try:
        bound_message_history([], max_chars=0)
    except ValueError as exc:
        assert "max_chars" in str(exc)
    else:
        raise AssertionError("Expected invalid max_chars to raise")
