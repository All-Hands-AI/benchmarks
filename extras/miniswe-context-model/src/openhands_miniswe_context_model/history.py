"""History bounding that preserves tool-call protocol boundaries."""

from __future__ import annotations

import json
from collections.abc import Sequence
from typing import Any


ELISION_NOTICE = (
    "[Earlier assistant and tool interactions were omitted to stay within the "
    "model context window. Their effects remain in the current workspace.]"
)


def _message_size(message: dict[str, Any]) -> int:
    return len(
        json.dumps(
            message,
            ensure_ascii=False,
            separators=(",", ":"),
            default=str,
        )
    )


def _history_units(messages: Sequence[dict[str, Any]]) -> list[list[dict[str, Any]]]:
    """Group assistant messages with their following tool results."""
    units: list[list[dict[str, Any]]] = []
    for message in messages:
        if (
            message.get("role") == "tool"
            and units
            and units[-1][0].get("role") == "assistant"
        ):
            units[-1].append(message)
        else:
            units.append([message])
    return units


def bound_message_history(
    messages: Sequence[dict[str, Any]],
    *,
    max_chars: int,
    preserve_first: int = 2,
    min_recent_units: int = 8,
) -> list[dict[str, Any]]:
    """Drop the oldest complete turns when serialized history exceeds a budget.

    The initial system/task messages are always retained. Assistant tool calls and
    their tool results are grouped into atomic units, so trimming never leaves an
    orphaned tool response in the request sent to the model.
    """
    if max_chars <= 0:
        raise ValueError("max_chars must be positive")
    if preserve_first < 0:
        raise ValueError("preserve_first cannot be negative")
    if min_recent_units < 1:
        raise ValueError("min_recent_units must be at least one")

    copied = [dict(message) for message in messages]
    if sum(_message_size(message) for message in copied) <= max_chars:
        return copied

    header = copied[:preserve_first]
    units = _history_units(copied[preserve_first:])
    notice = {"role": "user", "content": ELISION_NOTICE}
    remaining = (
        max_chars
        - sum(_message_size(message) for message in header)
        - _message_size(notice)
    )

    kept_reversed: list[list[dict[str, Any]]] = []
    used = 0
    for unit in reversed(units):
        unit_size = sum(_message_size(message) for message in unit)
        if (
            kept_reversed
            and used + unit_size > remaining
            and len(kept_reversed) >= min_recent_units
        ):
            break
        kept_reversed.append(unit)
        used += unit_size

    kept = [message for unit in reversed(kept_reversed) for message in unit]
    dropped_count = len(copied) - len(header) - len(kept)
    if dropped_count <= 0:
        return copied

    notice["content"] += f" ({dropped_count} messages omitted.)"
    return [*header, notice, *kept]
