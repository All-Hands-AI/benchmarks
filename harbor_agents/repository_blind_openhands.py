# pyright: reportMissingImports=false, reportGeneralTypeIssues=false
"""Repository-blind OpenHands SDK agents for the SWE-rebench V2 study."""

from __future__ import annotations

import base64
from pathlib import Path
from typing import Any, override
from urllib.parse import urlparse

from harbor.agents.installed.openhands_sdk import OpenHandsSDK
from harbor.environments.base import BaseEnvironment
from harbor.models.agent.context import AgentContext
from harbor.models.task.config import NetworkMode, NetworkPolicy


FORBIDDEN_HOSTS = (
    "api.github.com",
    "bitbucket.org",
    "github.com",
    "githubusercontent.com",
    "gitlab.com",
    "raw.githubusercontent.com",
)
POLICY = """ANTI-LOOKUP RULE — VIOLATION MAKES THE RESULT INCORRECT:
Do not search for, browse, fetch, clone, or inspect this project, its issue, pull
request, commits, or patches on GitHub or another code-hosting site. Do not use
git remotes or network commands to obtain upstream code. General documentation
about languages, libraries, APIs, standards, and error messages is allowed.
The experiment audits search evidence and commands. Any project lookup sets the
final reward to zero even if the code passes hidden tests.
"""
TASK_REPOSITORIES = {
    "geoswift__geoswift-307": "GEOSwift/GEOSwift",
    "spectreconsole__spectre.console-1942": "spectreconsole/spectre.console",
    "juliasymbolics__symbolics.jl-1673": "JuliaSymbolics/Symbolics.jl",
    "scalameta__scalameta-4345": "scalameta/scalameta",
    "felangel__bloc-4648": "felangel/bloc",
    "sciml__recursivearraytools.jl-494": "SciML/RecursiveArrayTools.jl",
    "detekt__detekt-8804": "detekt/detekt",
    "pwntester__octo.nvim-1175": "pwntester/octo.nvim",
}


def resolve_task_id(session_id: str) -> str:
    truncated_task_id = session_id.rsplit("__", 2)[0]
    return next(
        (
            task_id
            for task_id in TASK_REPOSITORIES
            if task_id.startswith(truncated_task_id)
        ),
        "",
    )


def audit_search(
    payload: dict[str, object], repository: str, instance_id: str
) -> list[str]:
    owner, name = (part.lower() for part in repository.split("/", 1))
    identifiers = (repository.lower(), instance_id.lower(), owner, name)
    violations: list[str] = []
    for hit in payload.get("hits", []):
        if not isinstance(hit, dict):
            violations.append("malformed search hit")
            continue
        url = str(hit.get("url", ""))
        parsed = urlparse(url)
        hostname = (parsed.hostname or "").lower()
        evidence = " ".join(
            str(hit.get(field, "")) for field in ("url", "title", "snippet")
        ).lower()
        if hostname in FORBIDDEN_HOSTS or hostname.endswith(
            (".github.com", ".githubusercontent.com")
        ):
            violations.append(f"forbidden code-host result: {url}")
        if any(identifier and identifier in evidence for identifier in identifiers):
            violations.append(f"project identifier in search result: {url}")
    return list(dict.fromkeys(violations))


class VerifierReadyOpenHandsSDK(OpenHandsSDK):
    """Control agent using the mounted SDK runtime and repository-blind prompt."""

    @override
    async def install(self, environment: BaseEnvironment) -> None:
        mounted = await environment.exec(
            command="/opt/openhands-sdk-venv/bin/python -c 'import openhands.sdk'"
        )
        if mounted.return_code != 0:
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
        await environment.set_network_policy(
            NetworkPolicy(network_mode=NetworkMode.PUBLIC)
        )
        await super().run(
            f"{POLICY}\nORIGINAL TASK\n{instruction}", environment, context
        )


class PplxOpenHandsSDK(VerifierReadyOpenHandsSDK):
    """Treatment agent required to use an audited PPLX wrapper while solving."""

    @staticmethod
    def _wrapper_source(repository: str, instance_id: str) -> str:
        return f"""#!/opt/openhands-sdk-venv/bin/python
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse

REAL = "/opt/openhands-sdk-venv/bin/pplx"
AUDIT = Path("/logs/agent/pplx_searches.jsonl")
REPOSITORY = {repository!r}
INSTANCE_ID = {instance_id!r}
FORBIDDEN_HOSTS = {FORBIDDEN_HOSTS!r}
owner, name = REPOSITORY.lower().split("/", 1)
identifiers = (REPOSITORY.lower(), INSTANCE_ID.lower(), owner, name)
args = sys.argv[1:]
record = {{"argv": args, "query": "", "violations": [], "return_code": None}}
if len(args) < 3 or args[:2] != ["search", "web"]:
    record["violations"].append("only `pplx search web <query>` is allowed")
else:
    query_parts = [part for part in args[2:] if not part.startswith("-")]
    query = " ".join(query_parts).strip()
    record["query"] = query
    lowered = query.lower()
    if any(identifier and identifier in lowered for identifier in identifiers):
        record["violations"].append("project identifier in query")
    if re.search(r"https?://|#\\d+|\\b[0-9a-f]{{7,40}}\\b", lowered):
        record["violations"].append("URL, issue number, or commit hash in query")
    command = [
        REAL, "search", "web", "--limit", "8", "--max-tokens", "5000",
        "--excluded-domains", ",".join(FORBIDDEN_HOSTS), "--", query,
    ]
    if not record["violations"]:
        result = subprocess.run(command, capture_output=True, text=True, timeout=120)
        record["return_code"] = result.returncode
        record["stderr"] = result.stderr[-2000:]
        if result.returncode == 0:
            try:
                payload = json.loads(result.stdout)
                record["payload"] = payload
                for hit in payload.get("hits", []):
                    url = str(hit.get("url", ""))
                    host = (urlparse(url).hostname or "").lower()
                    evidence = " ".join(str(hit.get(k, "")) for k in ("url", "title", "snippet")).lower()
                    if host in FORBIDDEN_HOSTS or host.endswith((".github.com", ".githubusercontent.com")):
                        record["violations"].append(f"forbidden code-host result: {{url}}")
                    if any(identifier and identifier in evidence for identifier in identifiers):
                        record["violations"].append(f"project identifier in result: {{url}}")
            except Exception as exc:
                record["violations"].append(f"invalid PPLX JSON: {{exc}}")
        else:
            record["violations"].append("PPLX command failed")
AUDIT.parent.mkdir(parents=True, exist_ok=True)
with AUDIT.open("a") as stream:
    stream.write(json.dumps(record) + "\\n")
if record["violations"]:
    print(json.dumps({{"error": record["violations"]}}), file=sys.stderr)
    raise SystemExit(42)
print(json.dumps(record["payload"]))
"""

    @override
    async def install(self, environment: BaseEnvironment) -> None:
        await super().install(environment)
        session_id = self.session_id or ""
        instance_id = resolve_task_id(session_id)
        if not instance_id:
            raise RuntimeError(f"Unknown SWE-rebench task session: {session_id}")
        wrapper = self._wrapper_source(TASK_REPOSITORIES[instance_id], instance_id)
        encoded = base64.b64encode(wrapper.encode()).decode()
        result = await self.exec_as_root(
            environment,
            command=(
                "/opt/openhands-sdk-venv/bin/python -c "
                + repr(
                    "import base64,pathlib; "
                    f"pathlib.Path('/usr/local/bin/pplx').write_bytes(base64.b64decode({encoded!r})); "
                    "pathlib.Path('/usr/local/bin/pplx').chmod(0o755); "
                    "pathlib.Path('/logs/agent/pplx_required').touch()"
                )
            ),
        )
        if result.return_code != 0:
            raise RuntimeError("Failed to install audited PPLX wrapper")

    @override
    async def run(
        self,
        instruction: str,
        environment: BaseEnvironment,
        context: AgentContext,
    ) -> None:
        await environment.set_network_policy(
            NetworkPolicy(network_mode=NetworkMode.PUBLIC)
        )
        required = """MANDATORY PPLX USE:
During this task you must run `/usr/local/bin/pplx search web <general technical query>` at least once and use the returned evidence. You may run it multiple times. The wrapper rejects project identifiers, URLs, issue numbers, commit hashes, and code-host results. Do not bypass the wrapper or call the binary under `/opt` directly. A task with no successful audited PPLX call receives reward zero.
"""
        await OpenHandsSDK.run(
            self,
            f"{POLICY}\n{required}\nORIGINAL TASK\n{instruction}",
            environment,
            context,
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
        api_key = self._get_env("PERPLEXITY_API_KEY")
        if api_key is not None:
            env = dict(env or {})
            env["PERPLEXITY_API_KEY"] = api_key
        return await super().exec_as_agent(
            environment, command, env=env, cwd=cwd, timeout_sec=timeout_sec
        )
