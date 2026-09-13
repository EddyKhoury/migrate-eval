"""Migration and repair-loop orchestration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from migrate_eval.dataset import MigrationProblem
from migrate_eval.extract import ExtractionError, go_block
from migrate_eval.models.base import ModelAdapter
from migrate_eval.prompts import initial, repair
from migrate_eval.runner import RunResult, RunStatus, run_go_tests


@dataclass(frozen=True)
class MigrationAttempt:
    """Result of one migration or repair attempt."""

    task_id: str
    model_name: str
    prompt: str
    raw_response: str | None
    go_code: str | None
    run_result: RunResult
    iteration: int = 0


Runner = Callable[..., RunResult]


def _execute_prompt(
    *,
    problem: MigrationProblem,
    model: ModelAdapter,
    prompt: str,
    iteration: int,
    runner: Runner,
) -> MigrationAttempt:
    """Execute one model -> extraction -> oracle attempt."""

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
            iteration=iteration,
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
            iteration=iteration,
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
        iteration=iteration,
    )


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

    return _execute_prompt(
        problem=problem,
        model=model,
        prompt=prompt,
        iteration=0,
        runner=runner,
    )


def migrate(
    problem: MigrationProblem,
    model: ModelAdapter,
    *,
    iters: int,
    runner: Runner = run_go_tests,
) -> list[MigrationAttempt]:
    """Migrate a problem and perform up to ``iters`` repair rounds.

    Iteration 0 is always the initial migration attempt.

    If iteration 0 fails and repair iterations remain, the latest generated
    Go implementation and its RunResult are fed to the repair prompt.

    The loop stops immediately when an attempt passes.

    MODEL_ERROR and EXTRACT_ERROR attempts cannot be repaired because they do
    not provide extracted Go code, so the loop stops in those cases.
    """

    if iters < 0:
        raise ValueError("iters must be >= 0")

    first_attempt = migrate_once(
        problem,
        model,
        runner=runner,
    )

    attempts = [first_attempt]

    if first_attempt.run_result.status is RunStatus.PASS:
        return attempts

    previous_attempt = first_attempt

    for iteration in range(1, iters + 1):
        if previous_attempt.go_code is None:
            break

        prompt = repair(
            go_code=previous_attempt.go_code,
            run_result=previous_attempt.run_result,
        )

        attempt = _execute_prompt(
            problem=problem,
            model=model,
            prompt=prompt,
            iteration=iteration,
            runner=runner,
        )

        attempts.append(attempt)

        if attempt.run_result.status is RunStatus.PASS:
            break

        previous_attempt = attempt

    return attempts