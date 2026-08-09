# pyright: reportMissingImports=false, reportGeneralTypeIssues=false
"""Perplexity-enabled OpenHands SDK agent for Terminal-Bench experiments."""

from __future__ import annotations

import base64
import json
import re
import shlex
from pathlib import Path
from typing import Any, override

from harbor.agents.installed.openhands_sdk import OpenHandsSDK
from harbor.environments.base import BaseEnvironment
from harbor.models.agent.context import AgentContext

from harbor_agents.pplx_command import build_bootstrap_search_command


class PplxOpenHandsSDK(OpenHandsSDK):
    """OpenHands SDK with a pinned ``pplx`` binary and scoped API-key forwarding."""

    PPLX_VERSION = "v0.2.2"

    @staticmethod
    def _bootstrap_query(instruction: str) -> str:
        """Build a bounded, task-specific query without another model call."""
        return re.sub(r"\s+", " ", instruction).strip()[:300]

    @classmethod
    def _install_command(cls) -> str:
        """Install the CLI using only the portable Python runtime."""
        script = f"""import hashlib
import os
import ssl
import urllib.request

import certifi

asset = "pplx-x86_64-linux-gnu.bin"
base = "https://github.com/perplexityai/perplexity-cli/releases/download/{cls.PPLX_VERSION}"
mounted_binary = "/opt/openhands-sdk-venv/bin/pplx"
if os.path.isfile(mounted_binary):
    with open(mounted_binary, "rb") as source:
        binary = source.read()
else:
    context = ssl.create_default_context(cafile=certifi.where())
    with urllib.request.urlopen(f"{{base}}/SHA256SUMS", timeout=60, context=context) as response:
        checksum_lines = response.read().decode().splitlines()
    expected = next(line.split()[0] for line in checksum_lines if line.split()[-1] == asset)
    with urllib.request.urlopen(f"{{base}}/{{asset}}", timeout=120, context=context) as response:
        binary = response.read()
    actual = hashlib.sha256(binary).hexdigest()
    if actual != expected:
        raise RuntimeError(f"pplx checksum mismatch: expected {{expected}}, got {{actual}}")
with open("/usr/local/bin/pplx", "wb") as output:
    output.write(binary)
os.chmod("/usr/local/bin/pplx", 0o755)
"""
        encoded = base64.b64encode(script.encode()).decode()
        return (
            "/opt/openhands-sdk-venv/bin/python -c "
            f"{shlex.quote(f'import base64; exec(base64.b64decode({encoded!r}))')}"
            " && pplx --version"
        )

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
            await environment.upload_file(
                source_path=local_copy, target_path="/installed-agent/run_agent.py"
            )
            await environment.exec(
                command="chmod +x /installed-agent/run_agent.py", user="root"
            )
        else:
            await super().install(environment)
        await self.exec_as_root(
            environment,
            command=self._install_command(),
        )

    @override
    async def run(
        self,
        instruction: str,
        environment: BaseEnvironment,
        context: AgentContext,
    ) -> None:
        """Require a successful CLI search and place its evidence in the prompt."""
        query = self._bootstrap_query(instruction)
        search = await self.exec_as_agent(
            environment,
            command=build_bootstrap_search_command(query),
            timeout_sec=120,
        )
        if search.return_code != 0:
            raise RuntimeError(
                "Required Perplexity bootstrap search failed: "
                f"{(search.stderr or '').strip()[:2000]}"
            )

        try:
            payload = json.loads(search.stdout or "")
        except json.JSONDecodeError as exc:
            raise RuntimeError(
                "Perplexity bootstrap search returned invalid JSON"
            ) from exc
        if not isinstance(payload, dict) or not isinstance(payload.get("hits"), list):
            raise RuntimeError("Perplexity bootstrap search JSON did not contain hits")

        research = json.dumps(payload, ensure_ascii=False)[:16000]
        augmented_instruction = f"""REQUIRED PERPLEXITY RESEARCH
The agent wrapper has already run a task-specific `pplx search web` command.
Use the results below when solving the task. You may run additional `pplx`
searches when useful. Do not expose the API key.

Search query: {query}
Search result JSON: {research}

ORIGINAL TASK
{instruction}"""
        await super().run(augmented_instruction, environment, context)

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
