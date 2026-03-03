#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import os
import sqlite3
from pathlib import Path
from typing import Iterable, List, Optional, Tuple


def fetch_one(conn: sqlite3.Connection, query: str, params: Tuple = ()) -> Optional[sqlite3.Row]:
    cur = conn.execute(query, params)
    return cur.fetchone()


def fetch_all(conn: sqlite3.Connection, query: str, params: Tuple = ()) -> List[sqlite3.Row]:
    cur = conn.execute(query, params)
    return cur.fetchall()


def export_query_to_csv(conn: sqlite3.Connection, query: str, params: Tuple, out_path: Path) -> int:
    cur = conn.execute(query, params)
    cols = [d[0] for d in cur.description]

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(cols)
        rows = cur.fetchall()
        for r in rows:
            w.writerow([r[c] for c in cols])
    return len(rows)


def detect_table(conn: sqlite3.Connection, name: str) -> bool:
    row = fetch_one(
        conn,
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?;",
        (name,),
    )
    return row is not None


def main() -> None:
    p = argparse.ArgumentParser(description="Exporta CSV a partir da base SQLite do projeto")
    p.add_argument(
        "--db",
        default="backend/data/experiments.sqlite",
        help="Caminho para a base SQLite",
    )
    p.add_argument(
        "--out-dir",
        default="experiments/analysis/out",
        help="Pasta de saída para os CSV",
    )
    p.add_argument(
        "--run-id",
        default=None,
        help="Exporta apenas uma run específica",
    )
    p.add_argument(
        "--scenario",
        default=None,
        help="Filtra por cenário, exemplo https_keepalive",
    )
    p.add_argument(
        "--latest",
        action="store_true",
        help="Exporta apenas a run mais recente (ignora --run-id)",
    )
    args = p.parse_args()

    db_path = Path(args.db)
    out_dir = Path(args.out_dir)

    if not db_path.exists():
        raise SystemExit(f"Base não encontrada em: {db_path}")

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row

    try:
        if not detect_table(conn, "runs") or not detect_table(conn, "messages"):
            raise SystemExit("Tabelas runs e messages não encontradas na base.")

        chosen_run_id: Optional[str] = None

        if args.latest:
            row = fetch_one(conn, "SELECT id FROM runs ORDER BY created_at DESC LIMIT 1;")
            if row is None:
                raise SystemExit("Não existem runs na base.")
            chosen_run_id = row["id"]
        elif args.run_id:
            chosen_run_id = args.run_id

        where_runs = []
        params_runs: List = []

        if chosen_run_id:
            where_runs.append("id = ?")
            params_runs.append(chosen_run_id)

        if args.scenario:
            where_runs.append("scenario = ?")
            params_runs.append(args.scenario)

        runs_where_sql = ""
        if where_runs:
            runs_where_sql = "WHERE " + " AND ".join(where_runs)

        runs_query = f"""
            SELECT
                id,
                created_at,
                device_id,
                scenario,
                transport,
                tls_enabled,
                connection_mode,
                payload_bytes,
                planned_messages,
                notes
            FROM runs
            {runs_where_sql}
            ORDER BY created_at ASC;
        """

        exported_runs = export_query_to_csv(
            conn,
            runs_query,
            tuple(params_runs),
            out_dir / "runs.csv",
        )

        messages_where = []
        params_messages: List = []

        if chosen_run_id:
            messages_where.append("run_id = ?")
            params_messages.append(chosen_run_id)

        if args.scenario:
            messages_where.append("run_id IN (SELECT id FROM runs WHERE scenario = ?)")
            params_messages.append(args.scenario)

        messages_where_sql = ""
        if messages_where:
            messages_where_sql = "WHERE " + " AND ".join(messages_where)

        messages_query = f"""
            SELECT
                id,
                ts,
                run_id,
                seq,
                payload_bytes,
                total_bytes,
                overhead_bytes,
                latency_ms,
                energy_mj
            FROM messages
            {messages_where_sql}
            ORDER BY run_id ASC, seq ASC;
        """

        exported_messages = export_query_to_csv(
            conn,
            messages_query,
            tuple(params_messages),
            out_dir / "messages.csv",
        )

        joined_query = f"""
            SELECT
                m.run_id,
                r.created_at AS run_created_at,
                r.device_id,
                r.scenario,
                r.transport,
                r.tls_enabled,
                r.connection_mode,
                r.payload_bytes AS run_payload_bytes,
                m.seq,
                m.ts AS msg_ts,
                m.payload_bytes AS msg_payload_bytes,
                m.total_bytes,
                m.overhead_bytes,
                m.latency_ms,
                m.energy_mj
            FROM messages m
            JOIN runs r ON r.id = m.run_id
            {messages_where_sql.replace("run_id", "m.run_id")}
            ORDER BY m.run_id ASC, m.seq ASC;
        """

        exported_joined = export_query_to_csv(
            conn,
            joined_query,
            tuple(params_messages),
            out_dir / "messages_with_run.csv",
        )

        print("Export concluído")
        print(f"runs.csv: {exported_runs} linhas")
        print(f"messages.csv: {exported_messages} linhas")
        print(f"messages_with_run.csv: {exported_joined} linhas")
        print(f"Saída em: {out_dir.resolve()}")

    finally:
        conn.close()


if __name__ == "__main__":
    main()
