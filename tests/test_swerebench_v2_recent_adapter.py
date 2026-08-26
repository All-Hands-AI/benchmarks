from __future__ import annotations

import json
from pathlib import Path

from harbor_agents.repository_blind_openhands import (
    TASK_REPOSITORIES,
    audit_search,
    repository_blind_query,
    resolve_task_id,
)


ROOT = Path(__file__).resolve().parents[1] / "adapters" / "swerebench_v2_recent"


def test_repository_blind_query_redacts_project_identifiers() -> None:
    query = repository_blind_query(
        "Fix Widget #42 from https://github.com/acme/widget commit abcdef123",
        "acme/widget",
        "acme__widget-42",
    )
    assert "widget" not in query.lower()
    assert "github" not in query.lower()
    assert "#42" not in query
    assert "abcdef123" not in query


def test_search_audit_rejects_code_hosts_and_mirrors() -> None:
    payload = {
        "hits": [
            {"url": "https://docs.python.org/3/", "title": "Python docs"},
            {"url": "https://github.com/acme/widget/issues/42"},
            {"url": "https://mirror.example/result", "title": "acme/widget fix"},
        ]
    }
    violations = audit_search(payload, "acme/widget", "acme__widget-42")
    assert len(violations) == 3


def test_truncated_harbor_session_resolves_full_task_id() -> None:
    assert (
        resolve_task_id("juliasymbolics__symbolics.jl-167__cT5EN9X__agent")
        == "juliasymbolics__symbolics.jl-1673"
    )


def test_selected_tasks_are_complete_and_do_not_expose_gold_in_instructions() -> None:
    task_dirs = sorted(path for path in (ROOT / "tasks").iterdir() if path.is_dir())
    assert {path.name for path in task_dirs} == set(TASK_REPOSITORIES)
    for task_dir in task_dirs:
        instruction = (task_dir / "instruction.md").read_text()
        assert "Project lookup is forbidden and disqualifying" in instruction
        assert "test_patch" not in instruction
        assert "FAIL_TO_PASS" not in instruction
        spec = json.loads((task_dir / "tests" / "spec.json").read_text())
        assert spec["instance_id"] == task_dir.name
        assert spec["repo"] == TASK_REPOSITORIES[task_dir.name]
        assert spec["test_patch"]
        assert (task_dir / "tests" / "test.sh").stat().st_mode & 0o111


def test_task_network_is_public_but_lookup_is_disqualifying() -> None:
    for task_toml in (ROOT / "tasks").glob("*/task.toml"):
        config = task_toml.read_text()
        assert '[agent]\ntimeout_sec = 7200\nnetwork_mode = "public"' in config
        assert '[verifier]\ntimeout_sec = 7200\nnetwork_mode = "public"' in config
