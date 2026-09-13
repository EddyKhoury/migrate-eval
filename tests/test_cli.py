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


def test_create_model_adapter_builds_ollama_adapter():
    adapter = cli.create_model_adapter(
        "ollama:qwen2.5-coder:14b"
    )

    assert isinstance(adapter, OllamaAdapter)
    assert adapter.name == "ollama:qwen2.5-coder:14b"


def test_create_model_adapter_builds_openai_adapter():
    adapter = cli.create_model_adapter(
        "openai:test-model"
    )

    assert isinstance(adapter, OpenAIAdapter)
    assert adapter.name == "openai:test-model"


def test_create_model_adapter_rejects_unknown_provider():
    with pytest.raises(ValueError):
        cli.create_model_adapter("unknown:model")


def test_cli_rejects_repair_iterations_in_milestone_2():
    result = runner.invoke(
        cli.app,
        [
            "run",
            "--model",
            "ollama:test-model",
            "--iters",
            "1",
        ],
    )

    assert result.exit_code != 0
    assert "supports only --iters 0" in result.output


def test_cli_runs_selected_problems_and_writes_jsonl(
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

    def fake_migrate_once(problem, adapter):
        status = (
            RunStatus.PASS
            if problem.task_id == "Go/0"
            else RunStatus.TEST_FAIL
        )

        return MigrationAttempt(
            task_id=problem.task_id,
            model_name=adapter.name,
            prompt="prompt",
            raw_response="response",
            go_code="package main",
            run_result=RunResult(
                status=status,
                stdout="",
                stderr="",
                duration=0.1,
            ),
        )

    monkeypatch.setattr(
        cli,
        "migrate_once",
        fake_migrate_once,
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
    assert "Go/0 PASS" in result.output
    assert "Go/1 TEST_FAIL" in result.output
    assert "pass@1: 1/2 (50.0%)" in result.output

    result_files = list(
        tmp_path.rglob("*.jsonl")
    )

    assert len(result_files) == 1

    lines = result_files[0].read_text(
        encoding="utf-8",
    ).splitlines()

    assert len(lines) == 2

    records = [
        json.loads(line)
        for line in lines
    ]

    assert records[0]["task_id"] == "Go/0"
    assert records[0]["status"] == "PASS"

    assert records[1]["task_id"] == "Go/1"
    assert records[1]["status"] == "TEST_FAIL"