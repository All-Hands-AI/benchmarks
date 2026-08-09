"""Build the task-side bootstrap for pinned TerminalBench verifier tools."""

from __future__ import annotations


VERIFIER_RUNTIME_ROOT = "/opt/openhands-sdk-venv"
VERIFIER_UV_VERSION = "0.9.5"
VERIFIER_PYTHON_VERSION = "3.13.9"
VERIFIER_PYTHON_MINOR = "3.13"


def build_verifier_bootstrap_command() -> str:
    """Link the mounted uv and Python into the locations used by task tests."""
    return f"""install -d -m 0755 /root/.local/bin /root/.local/share/uv/python && \
ln -sfn {VERIFIER_RUNTIME_ROOT}/bin/uv /root/.local/bin/uv && \
ln -sfn {VERIFIER_RUNTIME_ROOT}/bin/uvx /root/.local/bin/uvx && \
managed_python=$(find {VERIFIER_RUNTIME_ROOT}/verifier-python -mindepth 1 -maxdepth 1 \
-type d -name 'cpython-{VERIFIER_PYTHON_VERSION}-*' -print -quit) && \
test -n \"$managed_python\" && managed_name=${{managed_python##*/}} && \
managed_platform=${{managed_name#cpython-{VERIFIER_PYTHON_VERSION}-}} && \
rm -rf /root/.local/share/uv/python/\"$managed_name\" \
/root/.local/share/uv/python/cpython-{VERIFIER_PYTHON_MINOR}-\"$managed_platform\" && \
cp -a \"$managed_python\" /root/.local/share/uv/python/\"$managed_name\" && \
chmod -R u+w /root/.local/share/uv/python/\"$managed_name\" && \
ln -s \"$managed_name\" /root/.local/share/uv/python/cpython-{VERIFIER_PYTHON_MINOR}-\"$managed_platform\" && \
printf '%s\\n' 'export PATH=\"$HOME/.local/bin:$PATH\"' > /root/.local/bin/env && \
/root/.local/bin/uv --version | grep -F 'uv {VERIFIER_UV_VERSION}' && \
/root/.local/bin/uv python find {VERIFIER_PYTHON_MINOR} --no-project >/dev/null"""
