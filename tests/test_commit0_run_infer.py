"""Tests for commit0 run_infer test command helpers and the phased build pipeline.

The orchestration tests mirror test_phased_build.py / test_multimodal_phased_build.py:
commit0 now builds through the same shared phased pipeline (builder ->
base-image-minimal -> Dockerfile.agent-layer) as SWE-Bench.
"""

from pathlib import Path
from unittest.mock import patch

import pytest

from benchmarks.commit0 import build_images as commit0_build_images
from benchmarks.commit0.run_infer import get_pythonpath_prefix, normalize_pytest_cmd
from benchmarks.utils.build_utils import BuildOutput
from benchmarks.utils.version import get_phased_image_tag_prefix


def test_extract_custom_tag():
    tag = commit0_build_images.extract_custom_tag("docker.io/wentingzhao/tinydb:v0")
    assert tag == "commit0-tinydb"


def test_agent_server_image_tag_uses_phased_prefix():
    """The tag run_infer looks up must match what the phased assembly produces."""
    base_docker_image = commit0_build_images.get_base_docker_image("tinydb")
    custom_tag = commit0_build_images.extract_custom_tag(base_docker_image)

    tag = f"ghcr.io/example/agent-server:{get_phased_image_tag_prefix()}-{custom_tag}-source-minimal"

    assert tag == (
        "ghcr.io/example/agent-server:"
        f"{get_phased_image_tag_prefix()}-commit0-tinydb-source-minimal"
    )


class TestCommit0PhasedOrchestration:
    """Test that build_commit0_images orchestrates the three phases correctly."""

    @patch(
        "benchmarks.swebench.build_base_images.assemble_all_agent_images",
        return_value=0,
    )
    @patch(
        "benchmarks.swebench.build_base_images.build_all_base_images", return_value=0
    )
    @patch("benchmarks.swebench.build_base_images.build_builder_image")
    def test_happy_path_all_phases(self, mock_builder, mock_bases, mock_assemble):
        mock_builder.return_value = BuildOutput(
            base_image="builder",
            tags=["builder:abc"],
            error=None,
        )

        rc = commit0_build_images.build_commit0_images(
            base_images=["docker.io/wentingzhao/tinydb:v0"],
            target="source-minimal",
            build_dir=Path("/tmp/build"),
            image="ghcr.io/example/agent-server",
            push=True,
            max_workers=4,
            dry_run=False,
            force_build=True,
            max_retries=3,
        )

        assert rc == 0
        mock_builder.assert_called_once_with(push=True, force_build=True)
        mock_bases.assert_called_once()
        assert (
            mock_bases.call_args.kwargs["custom_tag_fn"]
            == commit0_build_images.extract_custom_tag
        )
        mock_assemble.assert_called_once()
        assert mock_assemble.call_args.kwargs["builder_tag"] == "builder:abc"
        assert mock_assemble.call_args.kwargs["target"] == "source-minimal"
        assert (
            mock_assemble.call_args.kwargs["custom_tag_fn"]
            == commit0_build_images.extract_custom_tag
        )

    def test_dry_run_lists_without_building(self, capsys):
        rc = commit0_build_images.build_commit0_images(
            base_images=["docker.io/wentingzhao/tinydb:v0"],
            target="source-minimal",
            build_dir=Path("/tmp/build"),
            image="ghcr.io/example/agent-server",
            push=False,
            max_workers=1,
            dry_run=True,
            force_build=False,
            max_retries=1,
        )

        assert rc == 0
        assert "docker.io/wentingzhao/tinydb:v0" in capsys.readouterr().out

    @patch("benchmarks.swebench.build_base_images.build_builder_image")
    def test_builder_failure_aborts_early(self, mock_builder):
        mock_builder.return_value = BuildOutput(
            base_image="builder",
            tags=[],
            error="build failed",
        )

        rc = commit0_build_images.build_commit0_images(
            base_images=["docker.io/wentingzhao/tinydb:v0"],
            target="source-minimal",
            build_dir=Path("/tmp/build"),
            image="ghcr.io/example/agent-server",
            push=False,
            max_workers=1,
            dry_run=False,
            force_build=False,
            max_retries=1,
        )

        assert rc == 1

    @patch(
        "benchmarks.swebench.build_base_images.build_all_base_images", return_value=1
    )
    @patch("benchmarks.swebench.build_base_images.build_builder_image")
    def test_base_failure_aborts_before_assembly(self, mock_builder, _bases):
        mock_builder.return_value = BuildOutput(
            base_image="builder",
            tags=["builder:abc"],
            error=None,
        )

        rc = commit0_build_images.build_commit0_images(
            base_images=["docker.io/wentingzhao/tinydb:v0"],
            target="source-minimal",
            build_dir=Path("/tmp/build"),
            image="ghcr.io/example/agent-server",
            push=False,
            max_workers=1,
            dry_run=False,
            force_build=False,
            max_retries=1,
        )

        assert rc == 1


def test_commit0_main_forwards_expected_build_args(monkeypatch):
    forwarded = {}

    monkeypatch.setattr(
        commit0_build_images,
        "collect_base_images",
        lambda **_: ["docker.io/example/base:v0"],
    )
    monkeypatch.setattr(
        commit0_build_images,
        "default_build_output_dir",
        lambda dataset, split: Path(f"/tmp/{dataset}/{split}"),
    )

    def fake_build_commit0_images(**kwargs):
        forwarded.update(kwargs)
        return 0

    monkeypatch.setattr(
        commit0_build_images, "build_commit0_images", fake_build_commit0_images
    )

    exit_code = commit0_build_images.main(
        [
            "--dataset",
            "dataset",
            "--split",
            "test",
            "--repo-split",
            "tinydb",
            "--image",
            "ghcr.io/example/agent-server",
            "--max-workers",
            "2",
            "--n-limit",
            "1",
        ]
    )

    assert exit_code == 0
    assert forwarded == {
        "base_images": ["docker.io/example/base:v0"],
        "target": "source-minimal",
        "build_dir": Path("/tmp/dataset/test"),
        "image": "ghcr.io/example/agent-server",
        "push": False,
        "max_workers": 2,
        "dry_run": False,
        "force_build": False,
        "max_retries": 3,
    }


@pytest.mark.parametrize(
    "input_cmd, expected",
    [
        ("pytest", "python -m pytest"),
        ("pytest3", "python -m pytest3"),
        ("python -m pytest", "python -m pytest"),
        ("mypytest", "mypytest"),
        ("pytest-xdist", "pytest-xdist"),
        ("pytest_runner", "pytest_runner"),
        (
            "pytest --assert=plain --ignore=setup.py",
            "python -m pytest --assert=plain --ignore=setup.py",
        ),
    ],
    ids=[
        "bare_pytest",
        "bare_pytest3",
        "already_module_form",
        "substring_mypytest",
        "substring_pytest-xdist",
        "substring_pytest_runner",
        "real-parsel-scenario",
    ],
)
def test_normalize_pytest_cmd(input_cmd, expected):
    assert normalize_pytest_cmd(input_cmd) == expected


@pytest.mark.parametrize(
    "src_dir, expected",
    [
        ("src/cachetools", "PYTHONPATH=src:$PYTHONPATH "),
        ("src", "PYTHONPATH=src:$PYTHONPATH "),
        ("", ""),
        ("lib/mypackage", ""),
        ("tests/src/data", ""),
    ],
    ids=[
        "src_layout",
        "bare_src",
        "empty_string",
        "no_src_dir",
        "src_not_at_start",
    ],
)
def test_get_pythonpath_prefix(src_dir, expected):
    assert get_pythonpath_prefix(src_dir) == expected
