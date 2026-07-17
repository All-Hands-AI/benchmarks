"""A LiteLLM mini-swe-agent model with bounded request history."""

from __future__ import annotations

from typing import Any

from minisweagent.models.litellm_model import (  # pyright: ignore[reportMissingImports]
    LitellmModel,
    LitellmModelConfig,
)
from pydantic import Field

from openhands_miniswe_context_model.history import bound_message_history


class ContextSafeLitellmModelConfig(LitellmModelConfig):
    max_history_chars: int = Field(default=500_000, gt=0)
    """Maximum serialized characters retained in requests to the model."""

    min_recent_history_units: int = Field(default=8, ge=1)
    """Minimum number of recent assistant/tool units to retain."""


class ContextSafeLitellmModel(LitellmModel):
    """Retain task setup and recent complete turns below a context-safe budget."""

    config: ContextSafeLitellmModelConfig

    def __init__(self, **kwargs: Any):
        super().__init__(config_class=ContextSafeLitellmModelConfig, **kwargs)

    def _prepare_messages_for_api(self, messages: list[dict]) -> list[dict]:
        prepared = super()._prepare_messages_for_api(messages)
        return bound_message_history(
            prepared,
            max_chars=self.config.max_history_chars,
            min_recent_units=self.config.min_recent_history_units,
        )
