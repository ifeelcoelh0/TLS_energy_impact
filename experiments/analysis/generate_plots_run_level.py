#!/usr/bin/env python3

from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import argparse

DEFAULT_IN = Path("experiments/analysis/out/messages_with_run.csv")
DEFAULT_OUT = Path("experiments/analysis/out/plots")

SCENARIO_ORDER = [
    "http_new",
    "http_keepalive",
    "https_new",
    "https_keepalive",
]

def ensure_columns(df, required):
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise SystemExit(f"Missing columns: {missing}")

def scenario_sort(index):
    ordered = [s for s in SCENARIO_ORDER if s in index]
    extras = sorted([s for s in index if s not in ordered])
    return ordered + extras

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--in", dest="in_path", default=str(DEFAULT_IN))
    parser.add_argument("--out-dir", dest="out_dir", default=str(DEFAULT_OUT))
    args = parser.parse_args()

    df = pd.read_csv(args.in_path)

    required = [
        "run_id",
        "scenario",
        "latency_ms",
        "energy_mj",
        "overhead_bytes",
        "msg_payload_bytes"
    ]
    ensure_columns(df, required)

    # ---- RUN LEVEL AGGREGATION ----
    run_level = df.groupby(["scenario", "run_id"]).agg(
        latency_mean=("latency_ms", "mean"),
        energy_mean=("energy_mj", "mean"),
        overhead_mean=("overhead_bytes", "mean")
    ).reset_index()

    # guardar tabela intermédia
    run_level.to_csv("experiments/analysis/out/run_level_summary.csv", index=False)

    # ---- SCENARIO LEVEL (mean + std across runs) ----
    scenario_level = run_level.groupby("scenario").agg(
        latency_mean=("latency_mean", "mean"),
        latency_std=("latency_mean", "std"),
        energy_mean=("energy_mean", "mean"),
        energy_std=("energy_mean", "std"),
        overhead_mean=("overhead_mean", "mean"),
        overhead_std=("overhead_mean", "std"),
        runs_count=("run_id", "count")
    )

    scenario_level = scenario_level.loc[scenario_sort(scenario_level.index)]

    print("\nRun-level summary:")
    print(scenario_level.round(4))

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    def plot(metric_mean, metric_std, title, ylabel, filename):
        fig, ax = plt.subplots()

        means = scenario_level[metric_mean]
        stds = scenario_level[metric_std]

        ax.bar(means.index, means, yerr=stds, capsize=5)
        ax.set_title(title)
        ax.set_ylabel(ylabel)
        ax.set_xlabel("Scenario")
        ax.grid(True, axis="y", linestyle=":")

        fig.tight_layout()
        fig.savefig(out_dir / f"{filename}.png", dpi=200)
        fig.savefig(out_dir / f"{filename}.svg")
        plt.close(fig)

    plot("latency_mean", "latency_std",
         "Latency per scenario (mean ± std across runs)",
         "Latency (ms)",
         "latency_run_level")

    plot("energy_mean", "energy_std",
         "Energy per scenario (mean ± std across runs)",
         "Energy (mJ)",
         "energy_run_level")

    plot("overhead_mean", "overhead_std",
         "Overhead per scenario (mean ± std across runs)",
         "Overhead (bytes)",
         "overhead_run_level")

    print(f"\nPlots saved in {out_dir}")

if __name__ == "__main__":
    main()

