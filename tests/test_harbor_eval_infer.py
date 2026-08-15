"""Tests for the generic Harbor evaluation phase."""

import json
from pathlib import Path

from benchmarks.harbor.eval_infer import (
    process_harbor_results,
    refresh_eval_output_from_harbor,
)


def test_refresh_reconverts_authoritative_harbor_results(tmp_path: Path) -> None:
    output_file = tmp_path / "output.jsonl"
    output_file.write_text(
        json.dumps(
            {
                "instance_id": "finished-before-timeout",
                "test_result": {},
                "error": "stale timeout classification",
            }
        )
        + "\n"
    )

    job_dir = tmp_path / "harbor_output" / "2026-01-01__00-00-00"
    trial_dir = job_dir / "finished-before-timeout__abc"
    trial_dir.mkdir(parents=True)
    (job_dir / "result.json").write_text(json.dumps({"id": "job"}))
    (trial_dir / "result.json").write_text(
        json.dumps(
            {
                "task_name": "finished-before-timeout",
                "trial_name": "finished-before-timeout__abc",
                "agent_result": {
                    "n_input_tokens": 10,
                    "n_output_tokens": 2,
                    "cost_usd": 0.0,
                },
                "verifier_result": {"rewards": {"reward": 1.0}},
                "exception_info": {
                    "exception_type": "AgentTimeoutError",
                    "exception_message": "Agent timed out after saving the answer",
                },
            }
        )
    )

    assert refresh_eval_output_from_harbor(output_file) is True

    report_file = tmp_path / "output.report.json"
    report = process_harbor_results(str(output_file), str(report_file))
    converted = json.loads(output_file.read_text())

    assert report["completed_instances"] == 1
    assert report["resolved_instances"] == 1
    assert report["error_instances"] == 0
    assert converted["test_result"]["agent_exception"]["exception_type"] == (
        "AgentTimeoutError"
    )


def test_refresh_keeps_existing_output_without_raw_harbor_results(
    tmp_path: Path,
) -> None:
    output_file = tmp_path / "output.jsonl"
    original = (
        json.dumps(
            {"instance_id": "existing", "test_result": {"passed": False}, "error": None}
        )
        + "\n"
    )
    output_file.write_text(original)

    assert refresh_eval_output_from_harbor(output_file) is False
    assert output_file.read_text() == original
