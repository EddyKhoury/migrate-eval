"""Command-line interface for migrate-eval."""

from __future__ import annotations

from concurrent.futures import (
    FIRST_COMPLETED,
    ThreadPoolExecutor,
    wait,
)
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import typer
from dotenv import load_dotenv

from migrate_eval.cache import CachedModelAdapter
from migrate_eval.costs import (
    estimate_model_cost_usd,
    has_pricing,
)
from migrate_eval.dataset import (
    build_migration_problems,
    load_go_problems,
    load_java_problems,
)
from migrate_eval.loop import migrate
from migrate_eval.models.base import ModelAdapter
from migrate_eval.models.ollama_adapter import OllamaAdapter
from migrate_eval.models.openai_adapter import OpenAIAdapter
from migrate_eval.prompts import initial, repair
from migrate_eval.results import (
    append_attempt,
    prompt_config_hash,
    write_run_metadata,
)
from migrate_eval.runner import RunResult, RunStatus


app = typer.Typer(
    help="Evaluate LLM-assisted Java-to-Go migrations.",
)


@app.callback()
def main() -> None:
    """migrate-eval command-line interface."""


def create_model_adapter(model_spec: str) -> ModelAdapter:
    """Create a model adapter from a provider:model specification."""

    if model_spec.startswith("ollama:"):
        model_name = model_spec.removeprefix("ollama:")

        if not model_name:
            raise ValueError(
                "Ollama model name cannot be empty"
            )

        return OllamaAdapter(
            model=model_name,
        )

    if model_spec.startswith("openai:"):
        model_name = model_spec.removeprefix("openai:")

        if not model_name:
            raise ValueError(
                "OpenAI model name cannot be empty"
            )

        return OpenAIAdapter(
            model=model_name,
        )

    raise ValueError(
        "model must use 'ollama:<name>' "
        "or 'openai:<name>'"
    )


def _new_run_id() -> str:
    """Create a compact unique identifier for one evaluation run."""

    timestamp = datetime.now(
        timezone.utc
    ).strftime(
        "%Y%m%dT%H%M%SZ"
    )

    suffix = uuid4().hex[:8]

    return f"{timestamp}-{suffix}"


def _safe_model_name(
    model_name: str,
) -> str:
    """Convert a model name into a filesystem-safe directory name."""

    return (
        model_name
        .replace(":", "__")
        .replace("/", "__")
    )


def _current_prompt_hash() -> str:
    """Hash the current initial and repair prompt configurations."""

    initial_prompt = initial(
        java_code="{java_code}",
        go_signature="{go_signature}",
    )

    representative_failure = RunResult(
        status=RunStatus.TEST_FAIL,
        stdout="{stdout}",
        stderr="{stderr}",
        duration=0.0,
    )

    repair_prompt = repair(
        go_code="{go_code}",
        run_result=representative_failure,
    )

    return prompt_config_hash(
        initial_prompt,
        repair_prompt,
    )


@app.command()
def run(
    model: str = typer.Option(
        ...,
        "--model",
        help="Model specification such as ollama:qwen2.5-coder:14b.",
    ),
    n: int = typer.Option(
        20,
        "--n",
        min=1,
        help="Number of benchmark problems to run.",
    ),
    iters: int = typer.Option(
        0,
        "--iters",
        min=0,
        help="Number of repair iterations.",
    ),
    workers: int = typer.Option(
        1,
        "--workers",
        min=1,
        help=(
            "Number of benchmark problems to evaluate concurrently. "
            "Repair iterations within one problem remain sequential."
        ),
    ),
    java_dataset: Path = typer.Option(
        Path(
            "data/humaneval_x/"
            "humaneval_java.jsonl.gz"
        ),
        "--java-dataset",
    ),
    go_dataset: Path = typer.Option(
        Path(
            "data/humaneval_x/"
            "humaneval_go.jsonl.gz"
        ),
        "--go-dataset",
    ),
    results_dir: Path = typer.Option(
        Path("results"),
        "--results-dir",
    ),
    max_cost: float | None = typer.Option(
        None,
        "--max-cost",
        help=(
            "Soft API cost limit in USD. "
            "Supported for models with configured pricing."
        ),
    ),
) -> None:
    """Run a Java-to-Go migration evaluation with optional repairs."""

    load_dotenv()

    try:
        adapter = create_model_adapter(model)
    except ValueError as exc:
        raise typer.BadParameter(
            str(exc)
        ) from exc

    if max_cost is not None:
        if max_cost <= 0:
            raise typer.BadParameter(
                "--max-cost must be greater than 0"
            )

        if not has_pricing(adapter.name):
            raise typer.BadParameter(
                "--max-cost is not supported for "
                f"{adapter.name}; pricing is not configured"
            )

    adapter = CachedModelAdapter(
        adapter,
        cache_dir=(
            results_dir
            / ".cache"
        ),
    )

    java_problems = load_java_problems(
        java_dataset
    )

    go_problems = load_go_problems(
        go_dataset
    )

    excluded_task_ids = {
        "Go/95",
    }

    problems = build_migration_problems(
        java_problems,
        go_problems,
        excluded_task_ids=excluded_task_ids,
    )

    selected = problems[:n]

    if not selected:
        raise typer.BadParameter(
            "no benchmark problems were selected"
        )

    run_id = _new_run_id()

    model_dir = (
        results_dir
        / _safe_model_name(adapter.name)
    )

    output_path = (
        model_dir
        / f"{run_id}.jsonl"
    )

    metadata_path = (
        model_dir
        / f"{run_id}.meta.json"
    )

    write_run_metadata(
        metadata_path,
        run_id=run_id,
        model=adapter.name,
        iters=iters,
        requested_n=n,
        task_ids=[
            problem.task_id
            for problem in selected
        ],
        excluded_task_ids=sorted(
            excluded_task_ids
        ),
        temperature=getattr(
            adapter,
            "temperature",
            None,
        ),
        prompt_hash=_current_prompt_hash(),
        max_cost_usd=max_cost,
        workers=workers,
    )

    attempts_by_problem = []
    estimated_cost_usd = 0.0
    cost_limit_reached = False

    def record_problem_result(
        *,
        position: int,
        problem,
        attempts,
    ) -> bool:
        """Persist one completed problem and update run cost."""

        nonlocal estimated_cost_usd

        attempts_by_problem.append(
            attempts
        )

        for attempt in attempts:
            append_attempt(
                output_path,
                attempt,
            )

            attempt_cost = estimate_model_cost_usd(
                model_name=attempt.model_name,
                input_tokens=attempt.input_tokens,
                output_tokens=attempt.output_tokens,
            )

            if (
                attempt_cost is not None
                and not attempt.cache_hit
            ):
                estimated_cost_usd += attempt_cost

        final_attempt = attempts[-1]

        typer.echo(
            f"[{position}/{len(selected)}] "
            f"{problem.task_id} "
            f"{final_attempt.run_result.status.value} "
            f"(iteration {final_attempt.iteration})"
        )

        return (
            max_cost is not None
            and estimated_cost_usd >= max_cost
        )

    if workers == 1:
        for position, problem in enumerate(
            selected,
            start=1,
        ):
            attempts = migrate(
                problem,
                adapter,
                iters=iters,
            )

            cost_limit_reached = (
                record_problem_result(
                    position=position,
                    problem=problem,
                    attempts=attempts,
                )
            )

            if cost_limit_reached:
                typer.echo(
                    "Cost limit reached after current problem: "
                    f"${estimated_cost_usd:.4f} "
                    f">= ${max_cost:.4f}. "
                    "Stopping before the next problem."
                )
                break

    else:
        cache_dir = (
            results_dir
            / ".cache"
        )

        def evaluate_problem(problem):
            # Each concurrent problem receives its own adapter.
            # Model adapters keep mutable per-call telemetry and
            # therefore must not be shared between worker threads.
            worker_adapter = CachedModelAdapter(
                create_model_adapter(
                    model
                ),
                cache_dir=cache_dir,
            )

            return migrate(
                problem,
                worker_adapter,
                iters=iters,
            )

        with ThreadPoolExecutor(
            max_workers=workers,
        ) as executor:
            next_index = 0
            pending = {}

            def submit_available() -> None:
                nonlocal next_index

                while (
                    next_index
                    < len(selected)
                    and len(pending)
                    < workers
                ):
                    position = (
                        next_index + 1
                    )

                    problem = selected[
                        next_index
                    ]

                    future = executor.submit(
                        evaluate_problem,
                        problem,
                    )

                    pending[future] = (
                        position,
                        problem,
                    )

                    next_index += 1

            submit_available()

            while pending:
                completed, _ = wait(
                    pending,
                    return_when=FIRST_COMPLETED,
                )

                for future in completed:
                    (
                        position,
                        problem,
                    ) = pending.pop(
                        future
                    )

                    attempts = (
                        future.result()
                    )

                    reached = (
                        record_problem_result(
                            position=position,
                            problem=problem,
                            attempts=attempts,
                        )
                    )

                    if reached:
                        cost_limit_reached = True

                if not cost_limit_reached:
                    submit_available()

        if cost_limit_reached:
            typer.echo(
                "Cost limit reached. "
                "No additional problems were started; "
                "already-running problems were allowed to finish. "
                f"Final estimated cost: "
                f"${estimated_cost_usd:.4f}."
            )

    typer.echo("")
    typer.echo(
        f"Model: {adapter.name}"
    )

    evaluated_count = len(
        attempts_by_problem
    )

    for iteration in range(
        iters + 1
    ):
        passes = 0

        for attempts in attempts_by_problem:
            passed_by_iteration = any(
                (
                    attempt.run_result.status
                    is RunStatus.PASS
                )
                and attempt.iteration <= iteration
                for attempt in attempts
            )

            if passed_by_iteration:
                passes += 1

        pass_rate = (
            passes
            / evaluated_count
        )

        typer.echo(
            f"pass@1 iteration {iteration}: "
            f"{passes}/{evaluated_count} "
            f"({pass_rate:.1%})"
        )

    if has_pricing(adapter.name):
        typer.echo(
            "Estimated API cost: "
            f"${estimated_cost_usd:.4f}"
        )

    typer.echo(
        f"Results: {output_path}"
    )

    typer.echo(
        f"Metadata: {metadata_path}"
    )