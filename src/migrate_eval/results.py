"""Persistence helpers for migration evaluation results."""

from __future__ import annotations

import json
from pathlib import Path

from migrate_eval.loop import MigrationAttempt


def attempt_to_record(
    attempt: MigrationAttempt,
    *,
    iteration: int = 0,
) -> dict:
    """Convert a MigrationAttempt into a JSON-serializable record."""

    return {
        "task_id": attempt.task_id,
        "model": attempt.model_name,
        "iteration": iteration,
        "prompt": attempt.prompt,
        "raw_response": attempt.raw_response,
        "go_code": attempt.go_code,
        "status": attempt.run_result.status.value,
        "stdout": attempt.run_result.stdout,
        "stderr": attempt.run_result.stderr,
        "duration": attempt.run_result.duration,
    }


def append_attempt(
    path: str | Path,
    attempt: MigrationAttempt,
    *,
    iteration: int = 0,
) -> None:
    """Append one migration attempt to a JSONL result file."""

    path = Path(path)

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    record = attempt_to_record(
        attempt,
        iteration=iteration,
    )

    with path.open(
        "a",
        encoding="utf-8",
    ) as file:
        json.dump(
            record,
            file,
            ensure_ascii=False,
        )
        file.write("\n")