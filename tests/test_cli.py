import json

import pytest
from typer.testing import CliRunner

from migrate_eval import cli
from migrate_eval.dataset import MigrationProblem
from migrate_eval.loop import MigrationAttempt
from migrate_eval.models.ollama_adapter import OllamaAdapter
from migrate_eval.models.openai_adapter import OpenAIAdapter
from migrate_eval.runner import RunResult, RunStatus


runner = CliRunner()


def make_attempt(
    *,
    task_id: str,
    model_name: str,
    iteration: int,
    status: RunStatus,
    go_code: str = "package main",
) -> MigrationAttempt:
    return MigrationAttempt(
        task_id=task_id,
        model_name=model_name,
        prompt=f"prompt iteration {iteration}",
        raw_response=f"response iteration {iteration}",
        go_code=go_code,
        run_result=RunResult(
            status=status,
            stdout="",
            stderr="",
            duration=0.1,
        ),
        iteration=iteration,
    )


def test_create_model_adapter_builds_ollama_adapter():
    adapter = cli.create_model_adapter(
        "ollama:qwen2.5-coder:14b"
    )

    assert isinstance(
        adapter,
        OllamaAdapter,
    )

    assert (
        adapter.name
        == "ollama:qwen2.5-coder:14b"
    )


def test_create_model_adapter_builds_openai_adapter():
    adapter = cli.create_model_adapter(
        "openai:test-model"
    )

    assert isinstance(
        adapter,
        OpenAIAdapter,
    )

    assert (
        adapter.name
        == "openai:test-model"
    )


def test_create_model_adapter_rejects_unknown_provider():
    with pytest.raises(
        ValueError
    ):
        cli.create_model_adapter(
            "unknown:model"
        )


def test_cli_single_shot_still_works(
    tmp_path,
    monkeypatch,
):
    problems = [
        MigrationProblem(
            task_id="Go/0",
            java_code="JAVA ZERO",
            go_signature="func Zero() int {",
            go_test="package main",
        ),
        MigrationProblem(
            task_id="Go/1",
            java_code="JAVA ONE",
            go_signature="func One() int {",
            go_test="package main",
        ),
    ]

    class FakeAdapter:
        name = "fake:model"
        temperature = 0.0

        def complete(
            self,
            prompt: str,
        ) -> str:
            return "unused"

    monkeypatch.setattr(
        cli,
        "create_model_adapter",
        lambda model_spec: FakeAdapter(),
    )

    monkeypatch.setattr(
        cli,
        "load_java_problems",
        lambda path: [],
    )

    monkeypatch.setattr(
        cli,
        "load_go_problems",
        lambda path: [],
    )

    monkeypatch.setattr(
        cli,
        "build_migration_problems",
        lambda java, go, excluded_task_ids=None: problems,
    )

    received_iters = []

    def fake_migrate(
        problem,
        adapter,
        *,
        iters,
    ):
        received_iters.append(
            iters
        )

        status = (
            RunStatus.PASS
            if problem.task_id == "Go/0"
            else RunStatus.TEST_FAIL
        )

        return [
            make_attempt(
                task_id=problem.task_id,
                model_name=adapter.name,
                iteration=0,
                status=status,
            )
        ]

    monkeypatch.setattr(
        cli,
        "migrate",
        fake_migrate,
    )

    result = runner.invoke(
        cli.app,
        [
            "run",
            "--model",
            "fake:model",
            "--n",
            "2",
            "--iters",
            "0",
            "--results-dir",
            str(tmp_path),
        ],
    )

    assert result.exit_code == 0

    assert received_iters == [
        0,
        0,
    ]

    assert (
        "Go/0 PASS (iteration 0)"
        in result.output
    )

    assert (
        "Go/1 TEST_FAIL (iteration 0)"
        in result.output
    )

    assert (
        "pass@1 iteration 0: "
        "1/2 (50.0%)"
        in result.output
    )

    result_files = list(
        tmp_path.rglob(
            "*.jsonl"
        )
    )

    assert len(
        result_files
    ) == 1

    lines = (
        result_files[0]
        .read_text(
            encoding="utf-8"
        )
        .splitlines()
    )

    assert len(lines) == 2

    records = [
        json.loads(line)
        for line in lines
    ]

    assert (
        records[0]["iteration"]
        == 0
    )

    assert (
        records[1]["iteration"]
        == 0
    )

    metadata_files = list(
        tmp_path.rglob(
            "*.meta.json"
        )
    )

    assert len(
        metadata_files
    ) == 1

    metadata = json.loads(
        metadata_files[0]
        .read_text(
            encoding="utf-8"
        )
    )

    assert (
        metadata["iters"]
        == 0
    )

    assert (
        metadata["task_ids"]
        == [
            "Go/0",
            "Go/1",
        ]
    )

    assert (
        metadata["excluded_task_ids"]
        == ["Go/95"]
    )


def test_cli_runs_repairs_logs_every_attempt_and_reports_cumulative_pass_rate(
    tmp_path,
    monkeypatch,
):
    problems = [
        MigrationProblem(
            task_id="Go/0",
            java_code="JAVA ZERO",
            go_signature="func Zero() int {",
            go_test="package main",
        ),
        MigrationProblem(
            task_id="Go/1",
            java_code="JAVA ONE",
            go_signature="func One() int {",
            go_test="package main",
        ),
    ]

    class FakeAdapter:
        name = "fake:model"
        temperature = 0.0

        def complete(
            self,
            prompt: str,
        ) -> str:
            return "unused"

    monkeypatch.setattr(
        cli,
        "create_model_adapter",
        lambda model_spec: FakeAdapter(),
    )

    monkeypatch.setattr(
        cli,
        "load_java_problems",
        lambda path: [],
    )

    monkeypatch.setattr(
        cli,
        "load_go_problems",
        lambda path: [],
    )

    monkeypatch.setattr(
        cli,
        "build_migration_problems",
        lambda java, go, excluded_task_ids=None: problems,
    )

    received_iters = []

    def fake_migrate(
        problem,
        adapter,
        *,
        iters,
    ):
        received_iters.append(
            iters
        )

        if problem.task_id == "Go/0":
            return [
                make_attempt(
                    task_id="Go/0",
                    model_name=adapter.name,
                    iteration=0,
                    status=RunStatus.PASS,
                )
            ]

        return [
            make_attempt(
                task_id="Go/1",
                model_name=adapter.name,
                iteration=0,
                status=RunStatus.TEST_FAIL,
            ),
            make_attempt(
                task_id="Go/1",
                model_name=adapter.name,
                iteration=1,
                status=RunStatus.PASS,
            ),
        ]

    monkeypatch.setattr(
        cli,
        "migrate",
        fake_migrate,
    )

    result = runner.invoke(
        cli.app,
        [
            "run",
            "--model",
            "fake:model",
            "--n",
            "2",
            "--iters",
            "3",
            "--results-dir",
            str(tmp_path),
        ],
    )

    assert result.exit_code == 0

    assert received_iters == [
        3,
        3,
    ]

    assert (
        "Go/0 PASS (iteration 0)"
        in result.output
    )

    assert (
        "Go/1 PASS (iteration 1)"
        in result.output
    )

    assert (
        "pass@1 iteration 0: "
        "1/2 (50.0%)"
        in result.output
    )

    assert (
        "pass@1 iteration 1: "
        "2/2 (100.0%)"
        in result.output
    )

    assert (
        "pass@1 iteration 2: "
        "2/2 (100.0%)"
        in result.output
    )

    assert (
        "pass@1 iteration 3: "
        "2/2 (100.0%)"
        in result.output
    )

    result_files = list(
        tmp_path.rglob(
            "*.jsonl"
        )
    )

    assert len(
        result_files
    ) == 1

    records = [
        json.loads(line)
        for line in (
            result_files[0]
            .read_text(
                encoding="utf-8"
            )
            .splitlines()
        )
    ]

    assert len(records) == 3

    assert [
        (
            record["task_id"],
            record["iteration"],
            record["status"],
        )
        for record in records
    ] == [
        (
            "Go/0",
            0,
            "PASS",
        ),
        (
            "Go/1",
            0,
            "TEST_FAIL",
        ),
        (
            "Go/1",
            1,
            "PASS",
        ),
    ]

    metadata_files = list(
        tmp_path.rglob(
            "*.meta.json"
        )
    )

    assert len(
        metadata_files
    ) == 1

    metadata = json.loads(
        metadata_files[0]
        .read_text(
            encoding="utf-8"
        )
    )

    assert (
        metadata["iters"]
        == 3
    )

    assert (
        metadata["selected_n"]
        == 2
    )


def test_cli_rejects_max_cost_when_pricing_is_unavailable(
    tmp_path,
    monkeypatch,
):
    class FakeAdapter:
        name = "fake:model"
        temperature = 0.0

        def complete(self, prompt: str) -> str:
            return "unused"

    monkeypatch.setattr(
        cli,
        "create_model_adapter",
        lambda model_spec: FakeAdapter(),
    )

    result = runner.invoke(
        cli.app,
        [
            "run",
            "--model",
            "fake:model",
            "--n",
            "1",
            "--max-cost",
            "1.00",
            "--results-dir",
            str(tmp_path),
        ],
    )

    assert result.exit_code != 0
    assert "pricing is not" in result.output
    assert "configured" in result.output


def test_cli_stops_after_cost_limit_and_uses_executed_denominator(
    tmp_path,
    monkeypatch,
):
    problems = [
        MigrationProblem(
            task_id="Go/0",
            java_code="JAVA ZERO",
            go_signature="func Zero() int {",
            go_test="package main",
        ),
        MigrationProblem(
            task_id="Go/1",
            java_code="JAVA ONE",
            go_signature="func One() int {",
            go_test="package main",
        ),
    ]

    class FakeAdapter:
        name = "openai:gpt-5.6-terra"
        temperature = None

        def complete(self, prompt: str) -> str:
            return "unused"

    monkeypatch.setattr(
        cli,
        "create_model_adapter",
        lambda model_spec: FakeAdapter(),
    )

    monkeypatch.setattr(
        cli,
        "load_java_problems",
        lambda path: [],
    )

    monkeypatch.setattr(
        cli,
        "load_go_problems",
        lambda path: [],
    )

    monkeypatch.setattr(
        cli,
        "build_migration_problems",
        lambda java, go, excluded_task_ids=None: problems,
    )

    executed = []

    def fake_migrate(
        problem,
        adapter,
        *,
        iters,
    ):
        executed.append(problem.task_id)

        return [
            MigrationAttempt(
                task_id=problem.task_id,
                model_name=adapter.name,
                prompt="prompt",
                raw_response="response",
                go_code="package main",
                run_result=RunResult(
                    status=RunStatus.PASS,
                    stdout="",
                    stderr="",
                    duration=0.1,
                ),
                iteration=0,
                model_duration=0.5,
                input_tokens=100_000,
                output_tokens=100_000,
            )
        ]

    monkeypatch.setattr(
        cli,
        "migrate",
        fake_migrate,
    )

    result = runner.invoke(
        cli.app,
        [
            "run",
            "--model",
            "openai:gpt-5.6-terra",
            "--n",
            "2",
            "--iters",
            "0",
            "--max-cost",
            "1.00",
            "--results-dir",
            str(tmp_path),
        ],
    )

    assert result.exit_code == 0

    # One fake call costs:
    # 100k * $2/M + 100k * $12/M = $1.40.
    assert executed == ["Go/0"]

    assert "Cost limit reached" in result.output
    assert "pass@1 iteration 0: 1/1 (100.0%)" in result.output
    assert "Estimated API cost: $1.4000" in result.output


def test_cli_does_not_charge_cache_hits_against_max_cost(
    tmp_path,
    monkeypatch,
):
    problems = [
        MigrationProblem(
            task_id="Go/0",
            java_code="JAVA ZERO",
            go_signature="func Zero() int {",
            go_test="package main",
        ),
        MigrationProblem(
            task_id="Go/1",
            java_code="JAVA ONE",
            go_signature="func One() int {",
            go_test="package main",
        ),
    ]

    class FakeAdapter:
        name = "openai:gpt-5.6-terra"
        temperature = None

        def complete(self, prompt: str) -> str:
            return "unused"

    monkeypatch.setattr(
        cli,
        "create_model_adapter",
        lambda model_spec: FakeAdapter(),
    )

    monkeypatch.setattr(
        cli,
        "load_java_problems",
        lambda path: [],
    )

    monkeypatch.setattr(
        cli,
        "load_go_problems",
        lambda path: [],
    )

    monkeypatch.setattr(
        cli,
        "build_migration_problems",
        lambda java, go, excluded_task_ids=None: problems,
    )

    executed = []

    def fake_migrate(
        problem,
        adapter,
        *,
        iters,
    ):
        executed.append(
            problem.task_id
        )

        return [
            MigrationAttempt(
                task_id=problem.task_id,
                model_name=adapter.name,
                prompt="prompt",
                raw_response="response",
                go_code="package main",
                run_result=RunResult(
                    status=RunStatus.PASS,
                    stdout="",
                    stderr="",
                    duration=0.1,
                ),
                input_tokens=100_000,
                output_tokens=100_000,
                cache_hit=True,
            )
        ]

    monkeypatch.setattr(
        cli,
        "migrate",
        fake_migrate,
    )

    result = runner.invoke(
        cli.app,
        [
            "run",
            "--model",
            "openai:gpt-5.6-terra",
            "--n",
            "2",
            "--max-cost",
            "0.01",
            "--results-dir",
            str(tmp_path),
        ],
    )

    assert result.exit_code == 0
    assert executed == [
        "Go/0",
        "Go/1",
    ]
    assert (
        "Estimated API cost: $0.0000"
        in result.output
    )
