"""Validate the Go execution oracle with HumanEval-X canonical solutions."""

from __future__ import annotations

import argparse
from pathlib import Path

from migrate_eval.dataset import (
    build_canonical_go_files,
    load_go_problems,
)
from migrate_eval.runner import RunStatus, run_go_tests


DEFAULT_DATASET = Path(
    "data/humaneval_x/humaneval_go.jsonl.gz"
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Run canonical HumanEval-X Go solutions through "
            "the migrate-eval Docker oracle."
        )
    )

    parser.add_argument(
        "--dataset",
        type=Path,
        default=DEFAULT_DATASET,
    )

    parser.add_argument(
        "--n",
        type=int,
        default=5,
        help="Number of problems to validate.",
    )

    parser.add_argument(
        "--timeout",
        type=float,
        default=30.0,
        help="Per-problem execution timeout in seconds.",
    )

    args = parser.parse_args()

    problems = load_go_problems(args.dataset)

    selected = problems[: args.n]

    results = []

    for problem in selected:
        task_id = problem["task_id"]

        go_code, go_test = build_canonical_go_files(
            problem
        )

        print(f"\n===== {task_id} =====")

        result = run_go_tests(
            go_code,
            go_test,
            timeout=args.timeout,
        )

        results.append(
            (
                task_id,
                result.status,
                result.duration,
            )
        )

        print("status:", result.status.value)
        print(f"duration: {result.duration:.2f}s")

        if result.status is not RunStatus.PASS:
            print("\nSTDOUT:")
            print(result.stdout)

            print("\nSTDERR:")
            print(result.stderr)

    print("\n===== SUMMARY =====")

    for task_id, status, duration in results:
        print(
            f"{task_id:8} "
            f"{status.value:15} "
            f"{duration:.2f}s"
        )

    passed = sum(
        status is RunStatus.PASS
        for _, status, _ in results
    )

    print(f"\nPassed: {passed}/{len(results)}")

    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
