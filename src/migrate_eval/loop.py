"""Single-shot migration orchestration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from migrate_eval.dataset import MigrationProblem
from migrate_eval.extract import ExtractionError, go_block
from migrate_eval.models.base import ModelAdapter
from migrate_eval.prompts import initial
from migrate_eval.runner import RunResult, RunStatus, run_go_tests


@dataclass(frozen=True)
class MigrationAttempt:
    """Result of one single-shot migration attempt."""

    task_id: str
    model_name: str
    prompt: str
    raw_response: str | None
    go_code: str | None
    run_result: RunResult


Runner = Callable[..., RunResult]


def migrate_once(
    problem: MigrationProblem,
    model: ModelAdapter,
    *,
    runner: Runner = run_go_tests,
) -> MigrationAttempt:
    """Perform one Java-to-Go migration attempt with no repair rounds."""

    prompt = initial(
        java_code=problem.java_code,
        go_signature=problem.go_signature,
    )

    try:
        raw_response = model.complete(prompt)
    except Exception as exc:
        return MigrationAttempt(
            task_id=problem.task_id,
            model_name=model.name,
            prompt=prompt,
            raw_response=None,
            go_code=None,
            run_result=RunResult(
                status=RunStatus.MODEL_ERROR,
                stdout="",
                stderr=str(exc),
                duration=0.0,
            ),
        )

    try:
        go_code = go_block(raw_response)
    except ExtractionError as exc:
        return MigrationAttempt(
            task_id=problem.task_id,
            model_name=model.name,
            prompt=prompt,
            raw_response=raw_response,
            go_code=None,
            run_result=RunResult(
                status=RunStatus.EXTRACT_ERROR,
                stdout="",
                stderr=str(exc),
                duration=0.0,
            ),
        )

    run_result = runner(
        go_code=go_code,
        go_test=problem.go_test,
    )

    return MigrationAttempt(
        task_id=problem.task_id,
        model_name=model.name,
        prompt=prompt,
        raw_response=raw_response,
        go_code=go_code,
        run_result=run_result,
    )