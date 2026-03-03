from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Any
from ..db.session import get_conn

router = APIRouter(prefix="/runs", tags=["runs"])

class RunOut(BaseModel):
    id: str
    created_at: str
    device_id: str
    scenario: str
    transport: str
    tls_enabled: bool
    connection_mode: str
    payload_bytes: int
    planned_messages: int | None
    notes: str | None

class MessageOut(BaseModel):
    id: int
    ts: str
    seq: int
    payload_bytes: int
    total_bytes: int
    overhead_bytes: int
    latency_ms: float
    energy_mj: float

class SummaryOut(BaseModel):
    messages_count: int
    avg_latency_ms: float | None
    avg_energy_mj: float | None
    total_overhead_bytes: int | None

class RunWithMessagesOut(BaseModel):
    run: RunOut
    summary: SummaryOut
    messages: list[MessageOut]

@router.get("/{run_id}", response_model=RunWithMessagesOut)
def get_run(run_id: str) -> Any:
    with get_conn() as conn:
        run_row = conn.execute(
            """
            SELECT id, created_at, device_id, scenario, transport, tls_enabled,
                   connection_mode, payload_bytes, planned_messages, notes
            FROM runs
            WHERE id = ?
            """,
            (run_id,),
        ).fetchone()

        if not run_row:
            raise HTTPException(status_code=404, detail="run_id not found")

        msg_rows = conn.execute(
            """
            SELECT id, ts, seq, payload_bytes, total_bytes, overhead_bytes, latency_ms, energy_mj
            FROM messages
            WHERE run_id = ?
            ORDER BY seq ASC
            """,
            (run_id,),
        ).fetchall()

        summary_row = conn.execute(
            """
            SELECT
              COUNT(*) AS messages_count,
              AVG(latency_ms) AS avg_latency_ms,
              AVG(energy_mj) AS avg_energy_mj,
              SUM(overhead_bytes) AS total_overhead_bytes
            FROM messages
            WHERE run_id = ?
            """,
            (run_id,),
        ).fetchone()

    run = RunOut(
        id=run_row["id"],
        created_at=run_row["created_at"],
        device_id=run_row["device_id"],
        scenario=run_row["scenario"],
        transport=run_row["transport"],
        tls_enabled=bool(run_row["tls_enabled"]),
        connection_mode=run_row["connection_mode"],
        payload_bytes=run_row["payload_bytes"],
        planned_messages=run_row["planned_messages"],
        notes=run_row["notes"],
    )

    messages = [
        MessageOut(
            id=r["id"],
            ts=r["ts"],
            seq=r["seq"],
            payload_bytes=r["payload_bytes"],
            total_bytes=r["total_bytes"],
            overhead_bytes=r["overhead_bytes"],
            latency_ms=r["latency_ms"],
            energy_mj=r["energy_mj"],
        )
        for r in msg_rows
    ]

    summary = SummaryOut(
        messages_count=summary_row["messages_count"],
        avg_latency_ms=summary_row["avg_latency_ms"],
        avg_energy_mj=summary_row["avg_energy_mj"],
        total_overhead_bytes=summary_row["total_overhead_bytes"],
    )

    return {"run": run, "summary": summary, "messages": messages}
