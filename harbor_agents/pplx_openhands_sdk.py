# pyright: reportMissingImports=false, reportGeneralTypeIssues=false
"""Perplexity-enabled OpenHands SDK agent for Terminal-Bench experiments."""

from __future__ import annotations

from pathlib import Path
from typing import Any, override

from harbor.agents.installed.openhands_sdk import OpenHandsSDK
from harbor.environments.base import BaseEnvironment


class PplxOpenHandsSDK(OpenHandsSDK):
    """OpenHands SDK with a pinned ``pplx`` binary and scoped API-key forwarding."""

    PPLX_VERSION = "v0.2.2"

    @override
    async def install(self, environment: BaseEnvironment) -> None:
        # A read-only evaluator-built venv is bind-mounted for batch evals.
        # Harbor's stock installer unnecessarily chowns that mount after its
        # existence probe, so install just the runner when it is available.
        mounted_runtime = await environment.exec(
            command="/opt/openhands-sdk-venv/bin/python -c 'import openhands.sdk'",
        )
        if mounted_runtime.return_code == 0:
            import harbor.agents.installed.openhands_sdk as adapter

            runner_path = Path(adapter.__file__).parent / "openhands_sdk_runner.py"
            local_copy = self.logs_dir / "run_agent.py"
            local_copy.write_text(runner_path.read_text())
            await environment.upload_file(source_path=local_copy, target_path="/installed-agent/run_agent.py")
            await environment.exec(command="chmod +x /installed-agent/run_agent.py", user="root")
        else:
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
