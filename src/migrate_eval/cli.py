"""Command-line interface for migrate-eval."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import typer
from dotenv import load_dotenv

from migrate_eval.dataset import (
    build_migration_problems,
    load_go_problems,
    load_java_problems,
)
from migrate_eval.loop import migrate_once
from migrate_eval.models.base import ModelAdapter
from migrate_eval.models.ollama_adapter import OllamaAdapter
from migrate_eval.models.openai_adapter import OpenAIAdapter
from migrate_eval.results import append_attempt
from migrate_eval.runner import RunStatus


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
            raise ValueError("Ollama model name cannot be empty")

        return OllamaAdapter(model=model_name)

    if model_spec.startswith("openai:"):
        model_name = model_spec.removeprefix("openai:")

        if not model_name:
            raise ValueError("OpenAI model name cannot be empty")

        return OpenAIAdapter(model=model_name)

    raise ValueError(
        "model must use 'ollama:<name>' or 'openai:<name>'"
    )


def _new_run_id() -> str:
    """Create a compact unique identifier for one evaluation run."""

    timestamp = datetime.now(timezone.utc).strftime(
        "%Y%m%dT%H%M%SZ"
    )

    suffix = uuid4().hex[:8]

    return f"{timestamp}-{suffix}"


def _safe_model_name(model_name: str) -> str:
    """Convert a model name into a filesystem-safe directory name."""

    return (
        model_name
        .replace(":", "__")
        .replace("/", "__")
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
    java_dataset: Path = typer.Option(
        Path("data/humaneval_x/humaneval_java.jsonl.gz"),
        "--java-dataset",
    ),
    go_dataset: Path = typer.Option(
        Path("data/humaneval_x/humaneval_go.jsonl.gz"),
        "--go-dataset",
    ),
    results_dir: Path = typer.Option(
        Path("results"),
        "--results-dir",
    ),
) -> None:
    """Run a single-shot Java-to-Go migration evaluation."""

    if iters != 0:
        raise typer.BadParameter(
            "Milestone 2 supports only --iters 0"
        )

    load_dotenv()

    try:
        adapter = create_model_adapter(model)
    except ValueError as exc:
        raise typer.BadParameter(str(exc)) from exc

    java_problems = load_java_problems(java_dataset)
    go_problems = load_go_problems(go_dataset)

    problems = build_migration_problems(
        java_problems,
        go_problems,
        excluded_task_ids={"Go/95"},
    )

    selected = problems[:n]

    if not selected:
        raise typer.BadParameter(
            "no benchmark problems were selected"
        )

    run_id = _new_run_id()

    output_path = (
        results_dir
        / _safe_model_name(adapter.name)
        / f"{run_id}.jsonl"
    )

    passes = 0

    for position, problem in enumerate(
        selected,
        start=1,
    ):
        attempt = migrate_once(
            problem,
            adapter,
        )

        append_attempt(
            output_path,
            attempt,
            iteration=0,
        )

        if attempt.run_result.status is RunStatus.PASS:
            passes += 1

        typer.echo(
            f"[{position}/{len(selected)}] "
            f"{problem.task_id} "
            f"{attempt.run_result.status.value}"
        )

    pass_rate = passes / len(selected)

    typer.echo("")
    typer.echo(f"Model: {adapter.name}")
    typer.echo(
        f"pass@1: {passes}/{len(selected)} "
        f"({pass_rate:.1%})"
    )
    typer.echo(f"Results: {output_path}")