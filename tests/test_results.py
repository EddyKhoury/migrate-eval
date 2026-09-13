import json

from migrate_eval.loop import MigrationAttempt
from migrate_eval.results import append_attempt, attempt_to_record
from migrate_eval.runner import RunResult, RunStatus


def make_attempt(
    *,
    task_id: str = "Go/0",
    status: RunStatus = RunStatus.PASS,
) -> MigrationAttempt:
    return MigrationAttempt(
        task_id=task_id,
        model_name="fake-model",
        prompt="migration prompt",
        raw_response="raw response",
        go_code="package main\n\nfunc Example() {}\n",
        run_result=RunResult(
            status=status,
            stdout="ok",
            stderr="",
            duration=0.25,
        ),
    )


def test_attempt_to_record_is_json_serializable():
    attempt = make_attempt()

    record = attempt_to_record(
        attempt,
        iteration=0,
    )

    encoded = json.dumps(record)

    assert encoded
    assert record["task_id"] == "Go/0"
    assert record["model"] == "fake-model"
    assert record["iteration"] == 0
    assert record["status"] == "PASS"
    assert record["duration"] == 0.25


def test_attempt_to_record_preserves_failure_status():
    attempt = make_attempt(
        status=RunStatus.COMPILE_ERROR,
    )

    record = attempt_to_record(attempt)

    assert record["status"] == "COMPILE_ERROR"


def test_append_attempt_creates_parent_directories(tmp_path):
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


def test_append_attempt_writes_json_line(tmp_path):
    path = tmp_path / "run.jsonl"

    append_attempt(
        path,
        make_attempt(),
    )

    lines = path.read_text(
        encoding="utf-8",
    ).splitlines()

    assert len(lines) == 1

    record = json.loads(lines[0])

    assert record["task_id"] == "Go/0"
    assert record["status"] == "PASS"


def test_append_attempt_appends_instead_of_overwriting(tmp_path):
    path = tmp_path / "run.jsonl"

    append_attempt(
        path,
        make_attempt(task_id="Go/0"),
    )

    append_attempt(
        path,
        make_attempt(task_id="Go/1"),
    )

    lines = path.read_text(
        encoding="utf-8",
    ).splitlines()

    assert len(lines) == 2

    first = json.loads(lines[0])
    second = json.loads(lines[1])

    assert first["task_id"] == "Go/0"
    assert second["task_id"] == "Go/1"