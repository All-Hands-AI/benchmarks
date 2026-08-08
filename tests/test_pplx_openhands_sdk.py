"""Tests for the Perplexity-enabled Harbor agent."""

import shlex

from harbor_agents.pplx_openhands_sdk import PplxOpenHandsSDK


def test_bootstrap_search_command_accepts_leading_dash_query() -> None:
    command = PplxOpenHandsSDK._bootstrap_search_command("- recover this model")

    assert shlex.split(command.split(" && ", maxsplit=1)[1]) == [
        "pplx",
        "search",
        "web",
        "-n",
        "5",
        "--output-dir",
        "/tmp/pplx-bootstrap",
        "--stdout-preview=500",
        "--",
        "- recover this model",
    ]
