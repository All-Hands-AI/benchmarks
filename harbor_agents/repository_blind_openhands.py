# pyright: reportMissingImports=false, reportGeneralTypeIssues=false
"""Repository-blind OpenHands SDK agents for the SWE-rebench V2 study."""

from __future__ import annotations

import json
import re
import shlex
from pathlib import Path
from typing import override
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
LLM_PROXY_HOST = "llm-proxy.eval.all-hands.dev"
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


def repository_blind_query(instruction: str, repository: str, instance_id: str) -> str:
    owner, name = repository.split("/", 1)
    text = instruction.rsplit("ORIGINAL TASK", 1)[-1]
    text = text.split("Relevant interfaces:", 1)[0]
    text = re.sub(r"https?://\S+", " ", text)
    text = re.sub(r"@[A-Za-z0-9_-]+", " ", text)
    text = re.sub(r"#\d+", " ", text)
    text = re.sub(r"\b[0-9a-fA-F]{7,40}\b", " ", text)
    for identifier in (repository, owner, name, instance_id):
        text = re.sub(re.escape(identifier), " ", text, flags=re.IGNORECASE)
    return re.sub(r"\s+", " ", text).strip()[:400]


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
            NetworkPolicy(
                network_mode=NetworkMode.ALLOWLIST,
                allowed_hosts=[LLM_PROXY_HOST],
            )
        )
        await super().run(
            f"{POLICY}\nORIGINAL TASK\n{instruction}", environment, context
        )


class PplxOpenHandsSDK(VerifierReadyOpenHandsSDK):
    """Treatment agent with one audited runner search before offline solving."""

    @override
    async def run(
        self,
        instruction: str,
        environment: BaseEnvironment,
        context: AgentContext,
    ) -> None:
        session_id = self.session_id or ""
        instance_id = resolve_task_id(session_id)
        if not instance_id:
            raise RuntimeError(f"Unknown SWE-rebench task session: {session_id}")
        repository = TASK_REPOSITORIES[instance_id]
        query = repository_blind_query(instruction, repository, instance_id)
        excluded = ",".join(FORBIDDEN_HOSTS)
        command = (
            "/opt/openhands-sdk-venv/bin/pplx search web "
            "--limit 8 --max-tokens 5000 "
            f"--excluded-domains {shlex.quote(excluded)} -- {shlex.quote(query)}"
        )
        api_key = self._get_env("PERPLEXITY_API_KEY")
        if api_key is None:
            raise ValueError("PERPLEXITY_API_KEY is required for treatment")
        search = await super().exec_as_agent(
            environment,
            command=command,
            env={"PERPLEXITY_API_KEY": api_key},
            timeout_sec=120,
        )
        if search.return_code != 0:
            raise RuntimeError(
                "Required repository-blind Perplexity search failed: "
                f"{(search.stderr or search.stdout or '').strip()[:2000]}"
            )
        try:
            payload = json.loads(search.stdout or "")
        except json.JSONDecodeError as exc:
            raise RuntimeError("Perplexity search returned invalid JSON") from exc
        if not isinstance(payload, dict) or not isinstance(payload.get("hits"), list):
            raise TypeError("Perplexity response must contain a hits list")

        violations = audit_search(payload, repository, instance_id)
        audit = {
            "query": query,
            "excluded_domains": list(FORBIDDEN_HOSTS),
            "violations": violations,
            "payload": payload,
        }
        audit_path = self.logs_dir / "pplx_search_audit.json"
        audit_path.write_text(json.dumps(audit, indent=2))
        await environment.upload_file(
            source_path=audit_path,
            target_path="/logs/agent/pplx_search_audit.json",
        )

        await environment.set_network_policy(
            NetworkPolicy(
                network_mode=NetworkMode.ALLOWLIST,
                allowed_hosts=[LLM_PROXY_HOST],
            )
        )
        evidence = ""
        if not violations:
            evidence = (
                "\nAUDITED GENERAL WEB EVIDENCE\n"
                + json.dumps(payload, ensure_ascii=False)[:16000]
            )
        await OpenHandsSDK.run(
            self,
            f"{POLICY}\nORIGINAL TASK\n{instruction}{evidence}",
            environment,
            context,
        )
