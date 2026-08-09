# pyright: reportMissingImports=false, reportGeneralTypeIssues=false
"""OpenHands SDK Harbor agent with pinned TerminalBench verifier tooling."""

from __future__ import annotations

from pathlib import Path
from typing import override

from harbor.agents.installed.openhands_sdk import OpenHandsSDK
from harbor.environments.base import BaseEnvironment
from harbor.models.agent.context import AgentContext

from harbor_agents.verifier_bootstrap import build_verifier_bootstrap_command


class VerifierReadyOpenHandsSDK(OpenHandsSDK):
    """OpenHands SDK agent that makes mounted verifier tools task-local."""

    @override
    async def install(self, environment: BaseEnvironment) -> None:
        mounted_runtime = await environment.exec(
            command="/opt/openhands-sdk-venv/bin/python -c 'import openhands.sdk'",
        )
        if mounted_runtime.return_code != 0:
            await super().install(environment)
            return

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

    @override
    async def run(
        self,
        instruction: str,
        environment: BaseEnvironment,
        context: AgentContext,
    ) -> None:
        mounted_tools = await environment.exec(
            command=(
                "test -x /opt/openhands-sdk-venv/bin/uv && "
                "test -d /opt/openhands-sdk-venv/verifier-python"
            )
        )
        if mounted_tools.return_code == 0:
            verifier_tools = await self.exec_as_root(
                environment,
                command=build_verifier_bootstrap_command(),
            )
            if verifier_tools.return_code != 0:
                raise RuntimeError(
                    "Failed to seed pinned TerminalBench verifier tools: "
                    f"{(verifier_tools.stderr or verifier_tools.stdout or '').strip()[:2000]}"
                )
        await super().run(instruction, environment, context)
