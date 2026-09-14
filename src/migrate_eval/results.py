"""Persistence helpers for migration evaluation results."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence

import pandas as pd

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


def load_results(
    paths: str | Path | Sequence[str | Path],
) -> pd.DataFrame:
    """Load one or more migrate-eval JSONL result files."""

    if isinstance(paths, (str, Path)):
        normalized_paths = [Path(paths)]
    else:
        normalized_paths = [Path(path) for path in paths]

    records: list[dict] = []

    for path in normalized_paths:
        with path.open("r", encoding="utf-8") as file:
            for line in file:
                if not line.strip():
                    continue

                record = json.loads(line)
                record["source_file"] = str(path)
                records.append(record)

    if not records:
        return pd.DataFrame()

    dataframe = pd.DataFrame(records)

    required = {
        "task_id",
        "model",
        "iteration",
        "status",
    }

    missing = required - set(dataframe.columns)

    if missing:
        raise ValueError(
            "result records are missing required columns: "
            + ", ".join(sorted(missing))
        )

    return dataframe


def cumulative_pass_rates(
    dataframe: pd.DataFrame,
    *,
    max_iteration: int | None = None,
) -> pd.DataFrame:
    """Calculate cumulative pass@1 by model and iteration."""

    if dataframe.empty:
        return pd.DataFrame(
            columns=[
                "model",
                "iteration",
                "passed",
                "total",
                "pass_rate",
            ]
        )

    required = {
        "task_id",
        "model",
        "iteration",
        "status",
    }

    missing = required - set(dataframe.columns)

    if missing:
        raise ValueError(
            "results dataframe is missing required columns: "
            + ", ".join(sorted(missing))
        )

    if max_iteration is None:
        max_iteration = int(dataframe["iteration"].max())

    if max_iteration < 0:
        raise ValueError("max_iteration must be >= 0")

    rows = []

    for model_name, model_df in dataframe.groupby(
        "model",
        sort=True,
    ):
        total = int(model_df["task_id"].nunique())

        for iteration in range(max_iteration + 1):
            eligible = model_df[
                model_df["iteration"] <= iteration
            ]

            passed = int(
                eligible.loc[
                    eligible["status"] == "PASS",
                    "task_id",
                ].nunique()
            )

            rows.append(
                {
                    "model": model_name,
                    "iteration": iteration,
                    "passed": passed,
                    "total": total,
                    "pass_rate": passed / total,
                }
            )

    return pd.DataFrame(rows)



def failure_taxonomy(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    """Summarize initial and final task status by model."""

    if dataframe.empty:
        return pd.DataFrame(
            columns=[
                "model",
                "stage",
                "status",
                "count",
                "total",
                "rate",
            ]
        )

    required = {
        "task_id",
        "model",
        "iteration",
        "status",
    }

    missing = required - set(dataframe.columns)

    if missing:
        raise ValueError(
            "results dataframe is missing required columns: "
            + ", ".join(sorted(missing))
        )

    rows = []

    for model_name, model_df in dataframe.groupby(
        "model",
        sort=True,
    ):
        total = int(
            model_df["task_id"].nunique()
        )

        initial = model_df[
            model_df["iteration"] == 0
        ]

        initial_counts = (
            initial["status"]
            .value_counts()
            .to_dict()
        )

        for status, count in sorted(
            initial_counts.items()
        ):
            rows.append(
                {
                    "model": model_name,
                    "stage": "initial",
                    "status": status,
                    "count": int(count),
                    "total": total,
                    "rate": int(count) / total,
                }
            )

        final_statuses = []

        for _, task_df in model_df.groupby(
            "task_id",
            sort=False,
        ):
            if (
                task_df["status"]
                == "PASS"
            ).any():
                final_statuses.append(
                    "PASS"
                )
            else:
                latest = task_df.sort_values(
                    "iteration"
                ).iloc[-1]

                final_statuses.append(
                    latest["status"]
                )

        final_counts = (
            pd.Series(
                final_statuses,
                dtype="object",
            )
            .value_counts()
            .to_dict()
        )

        for status, count in sorted(
            final_counts.items()
        ):
            rows.append(
                {
                    "model": model_name,
                    "stage": "final",
                    "status": status,
                    "count": int(count),
                    "total": total,
                    "rate": int(count) / total,
                }
            )

    return pd.DataFrame(rows)


def telemetry_summary(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    """Summarize token usage, cache use, and model latency by model."""

    if dataframe.empty:
        return pd.DataFrame(
            columns=[
                "model",
                "attempts",
                "fresh_attempts",
                "cache_hits",
                "total_input_tokens",
                "total_output_tokens",
                "mean_input_tokens",
                "mean_output_tokens",
                "mean_model_latency",
                "mean_fresh_model_latency",
            ]
        )

    required = {
        "model",
        "model_duration",
        "input_tokens",
        "output_tokens",
        "cache_hit",
    }

    missing = required - set(dataframe.columns)

    if missing:
        raise ValueError(
            "results dataframe is missing required columns: "
            + ", ".join(sorted(missing))
        )

    rows = []

    for model_name, model_df in dataframe.groupby(
        "model",
        sort=True,
    ):
        durations = pd.to_numeric(
            model_df["model_duration"],
            errors="coerce",
        )

        input_tokens = pd.to_numeric(
            model_df["input_tokens"],
            errors="coerce",
        )

        output_tokens = pd.to_numeric(
            model_df["output_tokens"],
            errors="coerce",
        )

        cache_hits = (
            model_df["cache_hit"]
            .fillna(False)
            .astype(bool)
        )

        fresh = ~cache_hits

        fresh_durations = durations[
            fresh
        ]

        rows.append(
            {
                "model": model_name,
                "attempts": int(
                    len(model_df)
                ),
                "fresh_attempts": int(
                    fresh.sum()
                ),
                "cache_hits": int(
                    cache_hits.sum()
                ),
                "total_input_tokens": int(
                    input_tokens.fillna(0).sum()
                ),
                "total_output_tokens": int(
                    output_tokens.fillna(0).sum()
                ),
                "mean_input_tokens": float(
                    input_tokens.mean()
                ),
                "mean_output_tokens": float(
                    output_tokens.mean()
                ),
                "mean_model_latency": float(
                    durations.mean()
                ),
                "mean_fresh_model_latency": float(
                    fresh_durations.mean()
                ),
            }
        )

    return pd.DataFrame(rows)



def evaluation_summary(
    dataframe: pd.DataFrame,
    *,
    max_iteration: int | None = None,
) -> pd.DataFrame:
    """Build one evaluation-summary row per model."""

    if dataframe.empty:
        return pd.DataFrame()

    pass_rates = cumulative_pass_rates(
        dataframe,
        max_iteration=max_iteration,
    )

    telemetry = telemetry_summary(
        dataframe
    )

    if max_iteration is None:
        max_iteration = int(
            pass_rates["iteration"].max()
        )

    rows = []

    for model_name, model_passes in pass_rates.groupby(
        "model",
        sort=True,
    ):
        model_passes = model_passes.sort_values(
            "iteration"
        )

        initial = model_passes[
            model_passes["iteration"] == 0
        ].iloc[0]

        final = model_passes[
            model_passes["iteration"]
            == max_iteration
        ].iloc[0]

        total_tasks = int(initial["total"])
        initial_passed = int(initial["passed"])
        final_passed = int(final["passed"])

        initial_failures = (
            total_tasks - initial_passed
        )

        repaired_failures = (
            final_passed - initial_passed
        )

        row = {
            "model": model_name,
            "total_tasks": total_tasks,
            "initial_passed": initial_passed,
            "final_passed": final_passed,
            "initial_failures": initial_failures,
            "repaired_failures": repaired_failures,
            "improvement_pp": (
                float(final["pass_rate"])
                - float(initial["pass_rate"])
            ) * 100.0,
            "repair_recovery_rate": (
                repaired_failures
                / initial_failures
                if initial_failures
                else 0.0
            ),
        }

        for iteration, pass_rate in model_passes[
            [
                "iteration",
                "pass_rate",
            ]
        ].itertuples(
            index=False,
            name=None,
        ):
            row[
                f"pass_rate_i{int(iteration)}"
            ] = float(
                pass_rate
            )

        model_telemetry = telemetry[
            telemetry["model"] == model_name
        ].iloc[0]

        for column in telemetry.columns:
            if column == "model":
                continue

            row[column] = model_telemetry[
                column
            ]

        rows.append(row)

    return pd.DataFrame(rows)
