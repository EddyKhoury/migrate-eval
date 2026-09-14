"""Persistence helpers for migration evaluation results."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence

from migrate_eval.loop import MigrationAttempt


def attempt_to_record(
    attempt: MigrationAttempt,
) -> dict:
    """Convert a MigrationAttempt into a JSON-serializable record."""

    return {
        "task_id": attempt.task_id,
        "model": attempt.model_name,
        "iteration": attempt.iteration,
        "model_duration": attempt.model_duration,
        "input_tokens": attempt.input_tokens,
        "output_tokens": attempt.output_tokens,
        "cache_hit": attempt.cache_hit,
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
) -> None:
    """Append one migration attempt to a JSONL result file."""

    path = Path(path)

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    record = attempt_to_record(attempt)

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


def prompt_config_hash(
    *prompt_texts: str,
) -> str:
    """Return a stable SHA-256 hash for the configured prompt texts."""

    payload = "\n---PROMPT-BOUNDARY---\n".join(prompt_texts)

    return hashlib.sha256(
        payload.encode("utf-8")
    ).hexdigest()


def write_run_metadata(
    path: str | Path,
    *,
    run_id: str,
    model: str,
    iters: int,
    requested_n: int,
    task_ids: Sequence[str],
    excluded_task_ids: Sequence[str],
    temperature: float | None,
    prompt_hash: str,
    max_cost_usd: float | None = None,
    workers: int = 1,
) -> None:
    """Write reproducibility metadata for one evaluation run."""

    path = Path(path)

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    metadata = {
        "run_id": run_id,
        "created_at_utc": datetime.now(
            timezone.utc
        ).isoformat(),
        "model": model,
        "iters": iters,
        "requested_n": requested_n,
        "selected_n": len(task_ids),
        "task_ids": list(task_ids),
        "excluded_task_ids": list(excluded_task_ids),
        "temperature": temperature,
        "prompt_hash": prompt_hash,
        "max_cost_usd": max_cost_usd,
        "workers": workers,
    }

    with path.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            metadata,
            file,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        file.write("\n")