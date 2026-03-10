#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List


def parse_ts(ts: str) -> datetime:
    return datetime.fromisoformat(ts)


def mean(values: List[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def main() -> None:
    p = argparse.ArgumentParser(description="Generate clean CSV for Excel analysis")
    p.add_argument(
        "--in-file",
        default="experiments/analysis/out/messages_with_run.csv",
        help="Input raw CSV"
    )
    p.add_argument(
        "--out-file",
        default="experiments/analysis/out/messages_with_run_clean.csv",
        help="Output clean CSV"
    )
    args = p.parse_args()

    in_path = Path(args.in_file)
    out_path = Path(args.out_file)

    if not in_path.exists():
      raise SystemExit(f"Input file not found: {in_path}")

    with in_path.open("r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    if not rows:
        raise SystemExit("Input CSV is empty")

    run_ts: Dict[str, List[datetime]] = defaultdict(list)
    run_latencies: Dict[str, List[float]] = defaultdict(list)
    run_message_count: Dict[str, int] = defaultdict(int)

    scenario_latencies: Dict[str, List[float]] = defaultdict(list)
    scenario_run_total_times: Dict[str, List[float]] = defaultdict(list)

    # Primeiro passe
    for row in rows:
        run_id = row["run_id"]
        scenario = row["scenario"]

        ts = parse_ts(row["msg_ts"])
        lat = float(row["latency_ms"])

        run_ts[run_id].append(ts)
        run_latencies[run_id].append(lat)
        run_message_count[run_id] += 1

        scenario_latencies[scenario].append(lat)

    run_total_time: Dict[str, float] = {}
    run_latency_mean: Dict[str, float] = {}
    scenario_latency_mean: Dict[str, float] = {}
    run_scenario: Dict[str, str] = {}

    # Mapear run -> scenario
    for row in rows:
        run_scenario[row["run_id"]] = row["scenario"]

    # Calcular métricas por run
    for run_id, ts_list in run_ts.items():
        total_time = (max(ts_list) - min(ts_list)).total_seconds()
        run_total_time[run_id] = total_time
        run_latency_mean[run_id] = mean(run_latencies[run_id])

        scenario = run_scenario[run_id]
        scenario_run_total_times[scenario].append(total_time)

    # Calcular métricas por scenario
    for scenario, lat_list in scenario_latencies.items():
        scenario_latency_mean[scenario] = mean(lat_list)

    scenario_total_time: Dict[str, float] = {}
    for scenario, run_times in scenario_run_total_times.items():
        scenario_total_time[scenario] = sum(run_times)

    out_cols = [
        "run_id",
        "scenario",
        "seq",
        "payload_bytes",
        "msg_created_at",
        "latency_ms",
        "run_latency_mean",
        "scenario_latency_mean",
        "run_total_time",
        "scenario_total_time",
        "run_message_count",
    ]

    out_path.parent.mkdir(parents=True, exist_ok=True)

    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=out_cols)
        writer.writeheader()

        for row in rows:
            run_id = row["run_id"]
            scenario = row["scenario"]

            out_row = {
                "run_id": run_id,
                "scenario": scenario,
                "seq": row["seq"],
                "payload_bytes": row["msg_payload_bytes"],
                "msg_created_at": row["msg_ts"],
                "latency_ms": row["latency_ms"],
                "run_latency_mean": f"{run_latency_mean[run_id]:.6f}",
                "scenario_latency_mean": f"{scenario_latency_mean[scenario]:.6f}",
                "run_total_time": f"{run_total_time[run_id]:.6f}",
                "scenario_total_time": f"{scenario_total_time[scenario]:.6f}",
                "run_message_count": run_message_count[run_id],
            }

            writer.writerow(out_row)

    print("Clean CSV generated")
    print(f"Input : {in_path}")
    print(f"Output: {out_path}")
    print(f"Rows  : {len(rows)}")


if __name__ == "__main__":
    main()
