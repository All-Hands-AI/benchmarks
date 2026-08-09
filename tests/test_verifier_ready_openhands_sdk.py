"""Tests for the stable TerminalBench verifier bootstrap."""

import shlex

from harbor_agents.verifier_bootstrap import build_verifier_bootstrap_command


def test_verifier_bootstrap_uses_pinned_runtime_tools() -> None:
    command = build_verifier_bootstrap_command()
    commands = shlex.split(command)

    assert "/opt/openhands-sdk-venv/bin/uv" in commands
    assert "/opt/openhands-sdk-venv/bin/uvx" in commands
    assert "/opt/openhands-sdk-venv/verifier-python" in commands
    assert "/root/.local/bin/env" in commands
    assert "uv 0.9.5" in commands
    assert "3.13" in commands
    assert "cpython-3.13.9-*" in commands
    assert "cp -a" in command
