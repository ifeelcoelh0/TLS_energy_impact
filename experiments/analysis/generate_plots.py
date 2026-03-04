#!/usr/bin/env python3
"""
Generate plots from exported CSV (messages_with_run.csv).

Input:
  experiments/analysis/out/messages_with_run.csv

Output:
  experiments/analysis/out/plots/*.png and *.svg

It groups by scenario and computes mean latency, mean energy, mean overhead.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt


DEFAULT_IN = Path("experiments/analysis/out/messages_with_run.csv")
DEFAULT_OUT_DIR = Path("experiments/analysis/out/plots")

SCENARIO_ORDER = [
    "http_new",
    "http_keepalive",
    "https_new",
    "https_keepalive",
]


def ensure_columns(df: pd.DataFrame, required: list[str]) -> None:
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise SystemExit(f"CSV is missing required columns: {missing}")


def safe_mkdir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def apply_filters(df: pd.DataFrame, scenario: str | None, run_id: str | None) -> pd.DataFrame:
    if scenario:
        df = df[df["scenario"] == scenario]
    if run_id:
        df = df[df["run_id"] == run_id]
    return df


def normalise_types(df: pd.DataFrame) -> pd.DataFrame:
    numeric_cols = ["latency_ms", "energy_mj", "msg_payload_bytes", "total_bytes", "overhead_bytes"]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df

def compute_overhead_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    overhead_ratio = overhead_bytes / msg_payload_bytes
    """
    ensure_columns(df, ["msg_payload_bytes", "overhead_bytes"])

    df["overhead_ratio"] = df["overhead_bytes"] / df["msg_payload_bytes"]
    return df



def scenario_sorted_index(index_values: list[str]) -> list[str]:
    order = [s for s in SCENARIO_ORDER if s in index_values]
    extras = sorted([s for s in index_values if s not in order])
    return order + extras


def plot_bar(series: pd.Series, title: str, ylabel: str, out_base: Path) -> None:
    """
    Saves bar plot to out_base.png and out_base.svg
    """
    fig = plt.figure()
    ax = fig.add_subplot(111)

    series.plot(kind="bar", ax=ax)
    ax.set_title(title)
    ax.set_ylabel(ylabel)
    ax.set_xlabel("Scenario")
    ax.grid(True, axis="y", linestyle=":", linewidth=0.8)

    fig.tight_layout()

    fig.savefig(str(out_base.with_suffix(".png")), dpi=200)
    fig.savefig(str(out_base.with_suffix(".svg")))
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate plots from messages_with_run.csv")
    parser.add_argument("--in", dest="in_path", default=str(DEFAULT_IN), help="Path to messages_with_run.csv")
    parser.add_argument("--out-dir", dest="out_dir", default=str(DEFAULT_OUT_DIR), help="Output directory for plots")
    parser.add_argument("--scenario", dest="scenario", default=None, help="Filter a single scenario")
    parser.add_argument("--run-id", dest="run_id", default=None, help="Filter a single run_id")
    parser.add_argument("--format-only", action="store_true", help="Only validate and print summary, no plots")

    args = parser.parse_args()

    in_path = Path(args.in_path)
    out_dir = Path(args.out_dir)

    if not in_path.exists():
        raise SystemExit(f"Input CSV not found: {in_path}")

    df = pd.read_csv(in_path)

    required = [
    "run_id",
    "scenario",
    "latency_ms",
    "energy_mj",
    "msg_payload_bytes",
    "total_bytes",
    "overhead_bytes",
    ]
    ensure_columns(df, required)

    df = normalise_types(df)
    df = apply_filters(df, args.scenario, args.run_id)
    df = df.dropna(subset=["scenario", "latency_ms", "energy_mj", "msg_payload_bytes", "total_bytes", "overhead_bytes"])

    if df.empty:
        raise SystemExit("No rows left after filters and cleaning")

    df = compute_overhead_columns(df)

    grouped = df.groupby("scenario", dropna=False).agg(
        latency_ms_mean=("latency_ms", "mean"),
        energy_mj_mean=("energy_mj", "mean"),
        overhead_bytes_mean=("overhead_bytes", "mean"),
        overhead_ratio_mean=("overhead_ratio", "mean"),
        messages_count=("scenario", "count"),
        runs_count=("run_id", "nunique"),
    )

    grouped = grouped.loc[scenario_sorted_index(grouped.index.tolist())]

    print("\nSummary by scenario")
    print(grouped.round(4).to_string())

    if args.format_only:
        return

    safe_mkdir(out_dir)

    plot_bar(
        grouped["latency_ms_mean"],
        "Average latency per scenario",
        "Latency (ms)",
        out_dir / "latency_ms_mean_by_scenario",
    )

    plot_bar(
        grouped["energy_mj_mean"],
        "Average energy per message per scenario",
        "Energy (mJ)",
        out_dir / "energy_mj_mean_by_scenario",
    )

    plot_bar(
        grouped["overhead_bytes_mean"],
        "Average overhead per message per scenario",
        "Overhead (bytes)",
        out_dir / "overhead_bytes_mean_by_scenario",
    )

    plot_bar(
        grouped["overhead_ratio_mean"],
        "Average overhead ratio per scenario",
        "Overhead ratio (bytes per payload byte)",
        out_dir / "overhead_ratio_mean_by_scenario",
    )

    print(f"\nPlots saved in: {out_dir.resolve()}")


if __name__ == "__main__":
    main()
