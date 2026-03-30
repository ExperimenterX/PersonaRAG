from __future__ import annotations

import argparse
from pathlib import Path
from typing import List

import pandas as pd
import matplotlib.pyplot as plt


METRIC_COLUMNS = [
    "exact_match",
    "token_f1",
    "support_rate",
    "context_answer_recall_at_k",
    "latency_seconds",
]


def _load_summary(csv_path: Path) -> pd.DataFrame:
    if not csv_path.exists():
        raise FileNotFoundError(f"Summary CSV not found: {csv_path}")

    df = pd.read_csv(csv_path)
    required = {"benchmark", "mode", *METRIC_COLUMNS}
    missing = required.difference(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    for col in METRIC_COLUMNS:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    return df


def _save_long_format(df: pd.DataFrame, output_dir: Path, run_name: str) -> Path:
    long_df = df.melt(
        id_vars=[c for c in df.columns if c not in METRIC_COLUMNS],
        value_vars=METRIC_COLUMNS,
        var_name="metric",
        value_name="value",
    )
    path = output_dir / f"{run_name}_long_metrics.csv"
    long_df.to_csv(path, index=False)
    return path


def _plot_metric(df: pd.DataFrame, metric: str, output_dir: Path, run_name: str) -> Path:
    pivot = (
        df.pivot_table(index="benchmark", columns="mode", values=metric, aggfunc="mean")
        .reindex(sorted(df["benchmark"].unique()))
    )

    ax = pivot.plot(kind="bar", figsize=(10, 6), rot=0)
    ax.set_title(f"Benchmark Comparison: {metric}")
    ax.set_xlabel("Benchmark")
    ax.set_ylabel(metric)
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    ax.legend(title="Mode", bbox_to_anchor=(1.02, 1), loc="upper left")
    plt.tight_layout()

    out_path = output_dir / f"{run_name}_{metric}.png"
    plt.savefig(out_path, dpi=180)
    plt.close()
    return out_path


def _plot_dashboard(df: pd.DataFrame, output_dir: Path, run_name: str) -> Path:
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    metrics = [
        "token_f1",
        "support_rate",
        "context_answer_recall_at_k",
        "latency_seconds",
    ]

    for ax, metric in zip(axes.flatten(), metrics):
        pivot = (
            df.pivot_table(index="benchmark", columns="mode", values=metric, aggfunc="mean")
            .reindex(sorted(df["benchmark"].unique()))
        )
        pivot.plot(kind="bar", ax=ax, rot=0)
        ax.set_title(metric)
        ax.set_xlabel("Benchmark")
        ax.set_ylabel(metric)
        ax.grid(axis="y", linestyle="--", alpha=0.35)
        ax.legend().remove()

    handles, labels = axes[0][0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", ncol=4, frameon=False)
    fig.suptitle("PersonaRAG Benchmark Metrics Dashboard", fontsize=14, y=0.98)
    plt.tight_layout(rect=[0, 0, 1, 0.94])

    out_path = output_dir / f"{run_name}_dashboard.png"
    plt.savefig(out_path, dpi=180)
    plt.close()
    return out_path


def _print_top_mode_summary(df: pd.DataFrame) -> None:
    print("\n=== Best Mode per Benchmark/Metric ===")
    grouped = df.groupby("benchmark")
    for benchmark, part in grouped:
        print(f"\n[{benchmark}]")
        for metric in ["exact_match", "token_f1", "support_rate", "context_answer_recall_at_k"]:
            row = part.sort_values(metric, ascending=False).iloc[0]
            print(f"  {metric:<28} -> {row['mode']} ({row[metric]:.4f})")
        row = part.sort_values("latency_seconds", ascending=True).iloc[0]
        print(f"  {'latency_seconds':<28} -> {row['mode']} ({row['latency_seconds']:.4f})")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Plot benchmark summary metrics into PNG charts.")
    parser.add_argument(
        "--input",
        type=str,
        default="server/output/benchmark_summary_combined.csv",
        help="Path to combined benchmark summary CSV.",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="server/output/plots",
        help="Directory to store generated plots and long-format data.",
    )
    parser.add_argument(
        "--run-name",
        type=str,
        default="benchmark_compare",
        help="Prefix used for output files.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    input_path = Path(args.input)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    df = _load_summary(input_path)
    _print_top_mode_summary(df)

    generated: List[Path] = []
    generated.append(_save_long_format(df, output_dir, args.run_name))

    for metric in METRIC_COLUMNS:
        generated.append(_plot_metric(df, metric, output_dir, args.run_name))

    generated.append(_plot_dashboard(df, output_dir, args.run_name))

    print("\n=== Generated Files ===")
    for path in generated:
        print(path)


if __name__ == "__main__":
    main()
