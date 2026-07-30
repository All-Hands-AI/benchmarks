# pyright: reportMissingImports=false, reportGeneralTypeIssues=false
"""Perplexity-enabled OpenHands SDK agent for Terminal-Bench experiments."""

from __future__ import annotations

from typing import Any, override

from harbor.agents.installed.openhands_sdk import OpenHandsSDK
from harbor.environments.base import BaseEnvironment


class PplxOpenHandsSDK(OpenHandsSDK):
    """OpenHands SDK with a pinned ``pplx`` binary and scoped API-key forwarding."""

    PPLX_VERSION = "v0.2.2"

    @override
    async def install(self, environment: BaseEnvironment) -> None:
        await super().install(environment)
        await self.exec_as_root(
            environment,
            command=(
                "set -euo pipefail; "
                "asset=pplx-x86_64-linux-gnu.bin; tmp=$(mktemp -d); "
                "trap 'rm -rf \"$tmp\"' EXIT; "
                f"base=https://github.com/perplexityai/perplexity-cli/releases/download/{self.PPLX_VERSION}; "
                'curl -fsSL --retry 3 "$base/SHA256SUMS" -o "$tmp/SHA256SUMS"; '
                'curl -fsSL --retry 3 "$base/$asset" -o "$tmp/$asset"; '
                '(cd "$tmp" && grep "  $asset$" SHA256SUMS | sha256sum -c -); '
                'install -m 0755 "$tmp/$asset" /usr/local/bin/pplx; '
                "pplx --version"
            ),
        )

    @override
    async def exec_as_agent(
        self,
        environment: BaseEnvironment,
        command: str,
        env: dict[str, str] | None = None,
        cwd: str | None = None,
        timeout_sec: int | None = None,
    ) -> Any:
        """Forward the key only to commands executed as the task-solving agent."""
        api_key = self._get_env("PERPLEXITY_API_KEY")
        if api_key is not None:
            env = dict(env or {})
            env["PERPLEXITY_API_KEY"] = api_key
        return await super().exec_as_agent(
            environment, command, env=env, cwd=cwd, timeout_sec=timeout_sec
        )
