"""Generate plots from migrate-eval JSONL result files."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter

from migrate_eval.results import (
    cumulative_pass_rates,
    failure_taxonomy,
    load_results,
)


def display_model_name(model: str) -> str:
    """Return a shorter display name for known evaluation models."""

    prefixes = (
        "openai:",
        "ollama:",
    )

    for prefix in prefixes:
        if model.startswith(prefix):
            return model.removeprefix(prefix)

    return model


def plot_pass_rate_vs_iteration(
    result_paths: list[str | Path],
    output_path: str | Path,
) -> Path:
    """Plot cumulative pass@1 against repair iteration."""

    dataframe = load_results(
        result_paths
    )

    if dataframe.empty:
        raise ValueError(
            "no evaluation records were loaded"
        )

    summary = cumulative_pass_rates(
        dataframe
    )

    output_path = Path(
        output_path
    )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    fig, ax = plt.subplots(
        figsize=(8, 5),
    )

    for model_name, model_df in summary.groupby(
        "model",
        sort=True,
    ):
        model_df = model_df.sort_values(
            "iteration"
        )

        ax.plot(
            model_df["iteration"],
            model_df["pass_rate"],
            marker="o",
            linewidth=2,
            label=display_model_name(
                model_name
            ),
        )

    max_iteration = int(
        summary["iteration"].max()
    )

    ax.set_xticks(
        range(max_iteration + 1)
    )

    ax.set_xlabel(
        "Repair iteration"
    )

    ax.set_ylabel(
        "Cumulative pass@1"
    )

    ax.yaxis.set_major_formatter(
        PercentFormatter(
            xmax=1.0
        )
    )

    ax.set_ylim(
        0.0,
        1.05,
    )

    ax.set_title(
        "Java-to-Go Migration Accuracy Across Repair Iterations"
    )

    ax.grid(
        axis="y",
        alpha=0.25,
    )

    ax.legend(
        title="Model"
    )

    fig.tight_layout()

    fig.savefig(
        output_path,
        dpi=160,
        bbox_inches="tight",
    )

    plt.close(fig)

    return output_path



def plot_failure_taxonomy(
    result_paths: list[str | Path],
    output_path: str | Path,
) -> Path:
    """Plot initial and final failure taxonomy for each model."""

    dataframe = load_results(
        result_paths
    )

    if dataframe.empty:
        raise ValueError(
            "no evaluation records were loaded"
        )

    taxonomy = failure_taxonomy(
        dataframe
    )

    failures = taxonomy[
        taxonomy["status"] != "PASS"
    ]

    model_names = sorted(
        dataframe["model"].unique()
    )

    bar_keys = [
        (model_name, stage)
        for model_name in model_names
        for stage in (
            "initial",
            "final",
        )
    ]

    labels = [
        (
            f"{display_model_name(model_name)}\n"
            f"{stage.title()}"
        )
        for model_name, stage in bar_keys
    ]

    preferred_status_order = [
        "COMPILE_ERROR",
        "TEST_FAIL",
        "TIMEOUT",
        "EXTRACT_ERROR",
        "MODEL_ERROR",
    ]

    observed_statuses = set(
        failures["status"].unique()
    )

    failure_statuses = [
        status
        for status in preferred_status_order
        if status in observed_statuses
    ]

    failure_statuses.extend(
        sorted(
            observed_statuses
            - set(failure_statuses)
        )
    )

    positions = list(
        range(len(bar_keys))
    )

    bottoms = [
        0
        for _ in bar_keys
    ]

    fig, ax = plt.subplots(
        figsize=(9, 5.5),
    )

    for status in failure_statuses:
        counts = []

        for model_name, stage in bar_keys:
            matching = failures[
                (failures["model"] == model_name)
                & (failures["stage"] == stage)
                & (failures["status"] == status)
            ]

            counts.append(
                int(
                    matching["count"].sum()
                )
            )

        ax.bar(
            positions,
            counts,
            bottom=bottoms,
            label=(
                status
                .replace("_", " ")
                .title()
            ),
        )

        bottoms = [
            bottom + count
            for bottom, count in zip(
                bottoms,
                counts,
            )
        ]

    for position, total in zip(
        positions,
        bottoms,
    ):
        ax.text(
            position,
            total + 0.5,
            str(total),
            ha="center",
            va="bottom",
        )

    ax.set_xticks(
        positions,
        labels,
    )

    ax.set_ylabel(
        "Failed benchmark tasks"
    )

    ax.set_title(
        "Failure Taxonomy Before and After Repair"
    )

    ax.grid(
        axis="y",
        alpha=0.25,
    )

    if failure_statuses:
        ax.legend(
            title="Failure status"
        )

    max_failures = max(
        bottoms,
        default=0,
    )

    ax.set_ylim(
        0,
        max_failures * 1.15 + 1,
    )

    output_path = Path(
        output_path
    )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    fig.tight_layout()

    fig.savefig(
        output_path,
        dpi=160,
        bbox_inches="tight",
    )

    plt.close(fig)

    return output_path

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Generate migrate-eval "
            "evaluation plots."
        )
    )

    parser.add_argument(
        "results",
        nargs="+",
        help=(
            "One or more evaluation "
            "JSONL result files."
        ),
    )

    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(
            "results/plots"
        ),
        help=(
            "Directory for generated "
            "plot files."
        ),
    )

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    pass_rate_output = (
        args.output_dir
        / "pass_rate_vs_iteration.png"
    )

    taxonomy_output = (
        args.output_dir
        / "failure_taxonomy.png"
    )

    generated_pass_rate = (
        plot_pass_rate_vs_iteration(
            args.results,
            pass_rate_output,
        )
    )

    generated_taxonomy = (
        plot_failure_taxonomy(
            args.results,
            taxonomy_output,
        )
    )

    print(
        f"Generated: {generated_pass_rate}"
    )

    print(
        f"Generated: {generated_taxonomy}"
    )


if __name__ == "__main__":
    main()
