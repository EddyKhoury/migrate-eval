import json

from migrate_eval.loop import MigrationAttempt
from migrate_eval.results import (
    append_attempt,
    attempt_to_record,
    prompt_config_hash,
    write_run_metadata,
)
from migrate_eval.runner import RunResult, RunStatus


def make_attempt(
    *,
    task_id: str = "Go/0",
    status: RunStatus = RunStatus.PASS,
    iteration: int = 0,
) -> MigrationAttempt:
    return MigrationAttempt(
        task_id=task_id,
        model_name="fake-model",
        prompt="migration prompt",
        raw_response="raw response",
        go_code=(
            "package main\n\n"
            "func Example() {}\n"
        ),
        run_result=RunResult(
            status=status,
            stdout="ok",
            stderr="",
            duration=0.25,
        ),
        iteration=iteration,
    )


def test_attempt_to_record_is_json_serializable():
    attempt = make_attempt()

    record = attempt_to_record(
        attempt,
    )

    encoded = json.dumps(record)

    assert encoded

    assert record["task_id"] == "Go/0"
    assert record["model"] == "fake-model"
    assert record["iteration"] == 0
    assert record["status"] == "PASS"
    assert record["duration"] == 0.25


def test_attempt_to_record_uses_attempt_iteration():
    attempt = make_attempt(
        iteration=2,
    )

    record = attempt_to_record(
        attempt,
    )

    assert record["iteration"] == 2


def test_attempt_to_record_preserves_failure_status():
    attempt = make_attempt(
        status=RunStatus.COMPILE_ERROR,
    )

    record = attempt_to_record(
        attempt
    )

    assert (
        record["status"]
        == "COMPILE_ERROR"
    )


def test_append_attempt_creates_parent_directories(
    tmp_path,
):
    path = (
        tmp_path
        / "results"
        / "fake-model"
        / "run.jsonl"
    )

    append_attempt(
        path,
        make_attempt(),
    )

    assert path.exists()


def test_append_attempt_writes_json_line(
    tmp_path,
):
    path = (
        tmp_path
        / "run.jsonl"
    )

    append_attempt(
        path,
        make_attempt(),
    )

    lines = path.read_text(
        encoding="utf-8",
    ).splitlines()

    assert len(lines) == 1

    record = json.loads(
        lines[0]
    )

    assert record["task_id"] == "Go/0"
    assert record["status"] == "PASS"
    assert record["iteration"] == 0


def test_append_attempt_appends_instead_of_overwriting(
    tmp_path,
):
    path = (
        tmp_path
        / "run.jsonl"
    )

    append_attempt(
        path,
        make_attempt(
            task_id="Go/0",
        ),
    )

    append_attempt(
        path,
        make_attempt(
            task_id="Go/1",
        ),
    )

    lines = path.read_text(
        encoding="utf-8",
    ).splitlines()

    assert len(lines) == 2

    first = json.loads(
        lines[0]
    )

    second = json.loads(
        lines[1]
    )

    assert (
        first["task_id"]
        == "Go/0"
    )

    assert (
        second["task_id"]
        == "Go/1"
    )


def test_prompt_config_hash_is_stable():
    first = prompt_config_hash(
        "initial prompt",
        "repair prompt",
    )

    second = prompt_config_hash(
        "initial prompt",
        "repair prompt",
    )

    assert first == second
    assert len(first) == 64


def test_prompt_config_hash_changes_when_prompt_changes():
    first = prompt_config_hash(
        "initial prompt",
        "repair prompt",
    )

    second = prompt_config_hash(
        "changed initial prompt",
        "repair prompt",
    )

    assert first != second


def test_write_run_metadata_writes_reproducibility_config(
    tmp_path,
):
    path = (
        tmp_path
        / "run.meta.json"
    )

    write_run_metadata(
        path,
        run_id="run-123",
        model="fake-model",
        iters=3,
        requested_n=20,
        task_ids=[
            "Go/0",
            "Go/1",
        ],
        excluded_task_ids=[
            "Go/95",
        ],
        temperature=0.0,
        prompt_hash="abc123",
    )

    metadata = json.loads(
        path.read_text(
            encoding="utf-8",
        )
    )

    assert (
        metadata["run_id"]
        == "run-123"
    )

    assert (
        metadata["model"]
        == "fake-model"
    )

    assert (
        metadata["iters"]
        == 3
    )

    assert (
        metadata["requested_n"]
        == 20
    )

    assert (
        metadata["selected_n"]
        == 2
    )

    assert metadata["task_ids"] == [
        "Go/0",
        "Go/1",
    ]

    assert (
        metadata["excluded_task_ids"]
        == ["Go/95"]
    )

    assert (
        metadata["temperature"]
        == 0.0
    )

    assert (
        metadata["prompt_hash"]
        == "abc123"
    )

    assert "created_at_utc" in metadata


def test_attempt_to_record_persists_model_telemetry():
    attempt = MigrationAttempt(
        task_id="Go/0",
        model_name="fake-model",
        prompt="migration prompt",
        raw_response="raw response",
        go_code="package main\n",
        run_result=RunResult(
            status=RunStatus.PASS,
            stdout="ok",
            stderr="",
            duration=0.25,
        ),
        iteration=1,
        model_duration=2.5,
        input_tokens=120,
        output_tokens=45,
    )

    record = attempt_to_record(attempt)

    assert record["model_duration"] == 2.5
    assert record["input_tokens"] == 120
    assert record["output_tokens"] == 45


def test_attempt_to_record_persists_cache_hit():
    attempt = MigrationAttempt(
        task_id="Go/0",
        model_name="fake-model",
        prompt="prompt",
        raw_response="response",
        go_code="package main\n",
        run_result=RunResult(
            status=RunStatus.PASS,
            stdout="",
            stderr="",
            duration=0.1,
        ),
        cache_hit=True,
    )

    record = attempt_to_record(attempt)

    assert record["cache_hit"] is True
