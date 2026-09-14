import json

from migrate_eval.loop import MigrationAttempt
from migrate_eval.results import (
    append_attempt,
    attempt_to_record,
    cumulative_pass_rates,
    evaluation_summary,
    failure_taxonomy,
    load_results,
    prompt_config_hash,
    telemetry_summary,
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



def test_load_results_reads_jsonl_into_dataframe(tmp_path):
    path = tmp_path / "run.jsonl"

    path.write_text(
        json.dumps({
            "task_id": "Go/0",
            "model": "model-a",
            "iteration": 0,
            "status": "PASS",
        })
        + "\n"
        + json.dumps({
            "task_id": "Go/1",
            "model": "model-a",
            "iteration": 0,
            "status": "TEST_FAIL",
        })
        + "\n",
        encoding="utf-8",
    )

    dataframe = load_results(path)

    assert len(dataframe) == 2
    assert set(dataframe["task_id"]) == {"Go/0", "Go/1"}
    assert (dataframe["source_file"] == str(path)).all()


def test_load_results_combines_multiple_files(tmp_path):
    first = tmp_path / "first.jsonl"
    second = tmp_path / "second.jsonl"

    first.write_text(
        json.dumps({
            "task_id": "Go/0",
            "model": "model-a",
            "iteration": 0,
            "status": "PASS",
        }) + "\n",
        encoding="utf-8",
    )

    second.write_text(
        json.dumps({
            "task_id": "Go/1",
            "model": "model-b",
            "iteration": 0,
            "status": "PASS",
        }) + "\n",
        encoding="utf-8",
    )

    dataframe = load_results([first, second])

    assert len(dataframe) == 2
    assert set(dataframe["model"]) == {
        "model-a",
        "model-b",
    }


def test_cumulative_pass_rates_counts_pass_by_iteration():
    import pandas as pd

    dataframe = pd.DataFrame([
        {
            "task_id": "Go/0",
            "model": "model-a",
            "iteration": 0,
            "status": "PASS",
        },
        {
            "task_id": "Go/1",
            "model": "model-a",
            "iteration": 0,
            "status": "TEST_FAIL",
        },
        {
            "task_id": "Go/1",
            "model": "model-a",
            "iteration": 1,
            "status": "PASS",
        },
        {
            "task_id": "Go/2",
            "model": "model-a",
            "iteration": 0,
            "status": "COMPILE_ERROR",
        },
    ])

    summary = cumulative_pass_rates(
        dataframe,
        max_iteration=2,
    )

    assert list(summary["passed"]) == [1, 2, 2]
    assert list(summary["total"]) == [3, 3, 3]


def test_cumulative_pass_rates_keeps_models_separate():
    import pandas as pd

    dataframe = pd.DataFrame([
        {
            "task_id": "Go/0",
            "model": "model-a",
            "iteration": 0,
            "status": "PASS",
        },
        {
            "task_id": "Go/0",
            "model": "model-b",
            "iteration": 0,
            "status": "TEST_FAIL",
        },
    ])

    summary = cumulative_pass_rates(
        dataframe,
        max_iteration=0,
    )

    model_a = summary[
        summary["model"] == "model-a"
    ].iloc[0]

    model_b = summary[
        summary["model"] == "model-b"
    ].iloc[0]

    assert model_a["pass_rate"] == 1.0
    assert model_b["pass_rate"] == 0.0



def test_failure_taxonomy_reports_initial_and_final_status():
    import pandas as pd

    dataframe = pd.DataFrame([
        {
            "task_id": "Go/0",
            "model": "model-a",
            "iteration": 0,
            "status": "PASS",
        },
        {
            "task_id": "Go/1",
            "model": "model-a",
            "iteration": 0,
            "status": "COMPILE_ERROR",
        },
        {
            "task_id": "Go/1",
            "model": "model-a",
            "iteration": 1,
            "status": "PASS",
        },
        {
            "task_id": "Go/2",
            "model": "model-a",
            "iteration": 0,
            "status": "TEST_FAIL",
        },
        {
            "task_id": "Go/2",
            "model": "model-a",
            "iteration": 1,
            "status": "TEST_FAIL",
        },
    ])

    summary = failure_taxonomy(
        dataframe
    )

    initial = summary[
        summary["stage"] == "initial"
    ]

    final = summary[
        summary["stage"] == "final"
    ]

    initial_counts = dict(
        zip(
            initial["status"],
            initial["count"],
        )
    )

    final_counts = dict(
        zip(
            final["status"],
            final["count"],
        )
    )

    assert initial_counts == {
        "COMPILE_ERROR": 1,
        "PASS": 1,
        "TEST_FAIL": 1,
    }

    assert final_counts == {
        "PASS": 2,
        "TEST_FAIL": 1,
    }


def test_failure_taxonomy_treats_any_pass_as_final_pass():
    import pandas as pd

    dataframe = pd.DataFrame([
        {
            "task_id": "Go/0",
            "model": "model-a",
            "iteration": 0,
            "status": "TEST_FAIL",
        },
        {
            "task_id": "Go/0",
            "model": "model-a",
            "iteration": 1,
            "status": "PASS",
        },
        {
            "task_id": "Go/0",
            "model": "model-a",
            "iteration": 2,
            "status": "TEST_FAIL",
        },
    ])

    summary = failure_taxonomy(
        dataframe
    )

    final = summary[
        summary["stage"] == "final"
    ]

    assert len(final) == 1
    assert final.iloc[0]["status"] == "PASS"
    assert final.iloc[0]["count"] == 1


def test_telemetry_summary_aggregates_tokens_and_latency():
    import pandas as pd

    dataframe = pd.DataFrame([
        {
            "model": "model-a",
            "model_duration": 2.0,
            "input_tokens": 100,
            "output_tokens": 20,
            "cache_hit": False,
        },
        {
            "model": "model-a",
            "model_duration": 4.0,
            "input_tokens": 200,
            "output_tokens": 40,
            "cache_hit": True,
        },
        {
            "model": "model-a",
            "model_duration": 6.0,
            "input_tokens": 300,
            "output_tokens": 60,
            "cache_hit": False,
        },
    ])

    summary = telemetry_summary(
        dataframe
    )

    row = summary.iloc[0]

    assert row["attempts"] == 3
    assert row["fresh_attempts"] == 2
    assert row["cache_hits"] == 1

    assert (
        row["total_input_tokens"]
        == 600
    )

    assert (
        row["total_output_tokens"]
        == 120
    )

    assert (
        row["mean_input_tokens"]
        == 200.0
    )

    assert (
        row["mean_output_tokens"]
        == 40.0
    )

    assert (
        row["mean_model_latency"]
        == 4.0
    )

    assert (
        row["mean_fresh_model_latency"]
        == 4.0
    )


def test_telemetry_summary_keeps_models_separate():
    import pandas as pd

    dataframe = pd.DataFrame([
        {
            "model": "model-a",
            "model_duration": 1.0,
            "input_tokens": 10,
            "output_tokens": 5,
            "cache_hit": False,
        },
        {
            "model": "model-b",
            "model_duration": 3.0,
            "input_tokens": 30,
            "output_tokens": 15,
            "cache_hit": False,
        },
    ])

    summary = telemetry_summary(
        dataframe
    )

    assert set(
        summary["model"]
    ) == {
        "model-a",
        "model-b",
    }

    assert len(summary) == 2



def test_evaluation_summary_combines_pass_and_telemetry():
    import pandas as pd

    dataframe = pd.DataFrame([
        {
            "task_id": "Go/0",
            "model": "model-a",
            "iteration": 0,
            "status": "PASS",
            "model_duration": 2.0,
            "input_tokens": 100,
            "output_tokens": 20,
            "cache_hit": False,
        },
        {
            "task_id": "Go/1",
            "model": "model-a",
            "iteration": 0,
            "status": "TEST_FAIL",
            "model_duration": 4.0,
            "input_tokens": 200,
            "output_tokens": 40,
            "cache_hit": False,
        },
        {
            "task_id": "Go/1",
            "model": "model-a",
            "iteration": 1,
            "status": "PASS",
            "model_duration": 6.0,
            "input_tokens": 300,
            "output_tokens": 60,
            "cache_hit": False,
        },
    ])

    summary = evaluation_summary(
        dataframe,
        max_iteration=1,
    )

    row = summary.iloc[0]

    assert row["model"] == "model-a"
    assert row["total_tasks"] == 2
    assert row["initial_passed"] == 1
    assert row["final_passed"] == 2
    assert row["initial_failures"] == 1
    assert row["repaired_failures"] == 1
    assert row["pass_rate_i0"] == 0.5
    assert row["pass_rate_i1"] == 1.0
    assert row["improvement_pp"] == 50.0
    assert row["repair_recovery_rate"] == 1.0
    assert row["attempts"] == 3
    assert row["fresh_attempts"] == 3
    assert row["cache_hits"] == 0
    assert row["total_input_tokens"] == 600
    assert row["total_output_tokens"] == 120
    assert row["mean_model_latency"] == 4.0
    assert row["mean_fresh_model_latency"] == 4.0


def test_evaluation_summary_keeps_models_separate():
    import pandas as pd

    dataframe = pd.DataFrame([
        {
            "task_id": "Go/0",
            "model": "model-a",
            "iteration": 0,
            "status": "PASS",
            "model_duration": 1.0,
            "input_tokens": 10,
            "output_tokens": 5,
            "cache_hit": False,
        },
        {
            "task_id": "Go/0",
            "model": "model-b",
            "iteration": 0,
            "status": "TEST_FAIL",
            "model_duration": 2.0,
            "input_tokens": 20,
            "output_tokens": 10,
            "cache_hit": False,
        },
    ])

    summary = evaluation_summary(
        dataframe,
        max_iteration=0,
    )

    assert len(summary) == 2

    assert set(
        summary["model"]
    ) == {
        "model-a",
        "model-b",
    }
