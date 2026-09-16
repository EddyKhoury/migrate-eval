"""Run a small real repair-loop demo for Go/2."""

from pathlib import Path

from dotenv import load_dotenv

from migrate_eval.cache import CachedModelAdapter
from migrate_eval.dataset import (
    build_migration_problems,
    load_go_problems,
    load_java_problems,
)
from migrate_eval.loop import migrate
from migrate_eval.models.openai_adapter import OpenAIAdapter
from migrate_eval.runner import RunStatus


TASK_ID = "Go/2"
MODEL = "gpt-5.6-terra"


def _failure_output(attempt, max_lines: int = 8) -> str:
    """Return a short compiler/test-output excerpt for the demo."""

    parts = []

    if attempt.run_result.stdout.strip():
        parts.append(attempt.run_result.stdout.strip())

    if attempt.run_result.stderr.strip():
        parts.append(attempt.run_result.stderr.strip())

    if not parts:
        return "(no compiler or test output)"

    lines = "\n".join(parts).splitlines()

    if len(lines) > max_lines:
        lines = lines[-max_lines:]

    return "\n".join(lines)


def main() -> None:
    load_dotenv()

    java_problems = load_java_problems(
        Path("data/humaneval_x/humaneval_java.jsonl.gz")
    )

    go_problems = load_go_problems(
        Path("data/humaneval_x/humaneval_go.jsonl.gz")
    )

    problems = build_migration_problems(
        java_problems,
        go_problems,
        excluded_task_ids={"Go/95"},
    )

    problem = next(
        problem
        for problem in problems
        if problem.task_id == TASK_ID
    )

    model = CachedModelAdapter(
        OpenAIAdapter(model=MODEL),
        cache_dir=Path("results/.cache"),
    )

    print()
    print("migrate-eval repair demo")
    print("========================")
    print(f"Task:  {TASK_ID}")
    print(f"Model: openai:{MODEL}")
    print()

    attempts = migrate(
        problem,
        model,
        iters=3,
    )

    for attempt in attempts:
        status = attempt.run_result.status.value

        print(
            f"Iteration {attempt.iteration} -> {status}"
        )

        if attempt.cache_hit:
            print("Model response: cached")
        else:
            print("Model response: fresh")

        if attempt.run_result.status is not RunStatus.PASS:
            print()
            print("Compiler / test feedback:")
            print("-------------------------")

            for line in _failure_output(attempt).splitlines():
                print(f"  {line}")

        print()

    final_status = attempts[-1].run_result.status

    print("========================")

    if final_status is RunStatus.PASS:
        print(
            f"PASS after {attempts[-1].iteration} repair iteration(s)"
        )
    else:
        print(
            f"Final status: {final_status.value}"
        )


if __name__ == "__main__":
    main()
