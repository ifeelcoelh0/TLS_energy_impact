from __future__ import annotations

import argparse
import sqlite3
from dataclasses import dataclass
from pathlib import Path

import pandas as pd


@dataclass
class Paths:
    repo_root: Path
    db_path: Path
    out_dir: Path


def find_repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def build_paths(db_path_arg: str | None) -> Paths:
    repo_root = find_repo_root()
    default_db = repo_root / "backend" / "data" / "experiments.sqlite"
    db_path = Path(db_path_arg).expanduser().resolve() if db_path_arg else default_db
    out_dir = repo_root / "experiments" / "analysis" / "out"
    out_dir.mkdir(parents=True, exist_ok=True)
    return Paths(repo_root=repo_root, db_path=db_path, out_dir=out_dir)


def read_tables(conn: sqlite3.Connection) -> tuple[pd.DataFrame, pd.DataFrame]:
    runs = pd.read_sql_query("SELECT * FROM runs;", conn)
    messages = pd.read_sql_query("SELECT * FROM messages;", conn)
    return runs, messages


def compute_run_stats(runs: pd.DataFrame, messages: pd.DataFrame) -> pd.DataFrame:
    agg = messages.groupby("run_id").agg(
        messages_count=("id", "count"),
        avg_latency_ms=("latency_ms", "mean"),
        std_latency_ms=("latency_ms", "std"),
        avg_energy_mj=("energy_mj", "mean"),
        std_energy_mj=("energy_mj", "std"),
        total_overhead_bytes=("overhead_bytes", "sum"),
        avg_overhead_bytes=("overhead_bytes", "mean"),
        min_latency_ms=("latency_ms", "min"),
        max_latency_ms=("latency_ms", "max"),
        min_energy_mj=("energy_mj", "min"),
        max_energy_mj=("energy_mj", "max"),
    ).reset_index()

    merged = runs.merge(agg, left_on="id", right_on="run_id", how="left")

    cols = [
        "id",
        "created_at",
        "scenario",
        "transport",
        "tls_enabled",
        "connection_mode",
        "payload_bytes",
        "planned_messages",
        "messages_count",
        "avg_latency_ms",
        "std_latency_ms",
        "avg_energy_mj",
        "std_energy_mj",
        "avg_overhead_bytes",
        "total_overhead_bytes",
        "min_latency_ms",
        "max_latency_ms",
        "min_energy_mj",
        "max_energy_mj",
        "notes",
    ]
    for c in cols:
        if c not in merged.columns:
            merged[c] = None

    merged = merged[cols].sort_values(["scenario", "created_at", "id"]).reset_index(drop=True)
    return merged


def compute_scenario_stats(run_stats: pd.DataFrame) -> pd.DataFrame:
    scen = run_stats.groupby("scenario").agg(
        runs_count=("id", "count"),
        total_messages=("messages_count", "sum"),
        avg_latency_ms=("avg_latency_ms", "mean"),
        std_latency_ms=("avg_latency_ms", "std"),
        avg_energy_mj=("avg_energy_mj", "mean"),
        std_energy_mj=("avg_energy_mj", "std"),
        avg_overhead_bytes=("avg_overhead_bytes", "mean"),
        total_overhead_bytes=("total_overhead_bytes", "sum"),
    ).reset_index()

    return scen.sort_values("scenario").reset_index(drop=True)


def save_csv(df: pd.DataFrame, path: Path) -> None:
    df.to_csv(path, index=False)


def print_table(df: pd.DataFrame, title: str, max_rows: int = 20) -> None:
    print()
    print(title)
    print("-" * len(title))
    if len(df) > max_rows:
        print(df.head(max_rows).to_string(index=False))
        print(f"... ({len(df)} rows total)")
    else:
        print(df.to_string(index=False))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default=None, help="Path to experiments.sqlite")
    args = parser.parse_args()

    paths = build_paths(args.db)
    if not paths.db_path.exists():
        raise SystemExit(f"Database not found: {paths.db_path}")

    conn = sqlite3.connect(paths.db_path)
    try:
        runs, messages = read_tables(conn)
    finally:
        conn.close()

    if runs.empty:
        raise SystemExit("No runs found in database.")
    if messages.empty:
        raise SystemExit("No messages found in database.")

    run_stats = compute_run_stats(runs, messages)
    scenario_stats = compute_scenario_stats(run_stats)

    save_csv(run_stats, paths.out_dir / "run_stats.csv")
    save_csv(scenario_stats, paths.out_dir / "scenario_stats.csv")

    print_table(scenario_stats, "Scenario summary")
    print_table(run_stats, "Run summary", max_rows=30)

    print()
    print(f"Saved CSV files to: {paths.out_dir}")


if __name__ == "__main__":
    main()
