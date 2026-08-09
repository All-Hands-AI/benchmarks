"""Shell command construction for Perplexity bootstrap searches."""

import shlex


def build_bootstrap_search_command(query: str) -> str:
    args = [
        "pplx",
        "search",
        "web",
        "-n",
        "5",
        "--output-dir",
        "/tmp/pplx-bootstrap",
        "--stdout-preview=500",
        "--",
        query,
    ]
    return f"mkdir -p /tmp/pplx-bootstrap && {shlex.join(args)}"
