from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ..db.session import get_conn

router = APIRouter()

class IngestMessage(BaseModel):
    run_id: str
    device_id: str
    scenario: str

    transport: str = Field(pattern="^(http|https)$")
    tls_enabled: bool
    connection_mode: str = Field(pattern="^(new|keepalive)$")

    seq: int = Field(ge=1)
    payload_bytes: int = Field(ge=0)
    total_bytes: int = Field(ge=0)

    latency_ms: float = Field(ge=0)
    energy_mj: float = Field(ge=0)

    planned_messages: int | None = Field(default=None, ge=1)
    notes: str | None = None

    payload: str | None = None

@router.post("/ingest")
def ingest(msg: IngestMessage):
    if msg.total_bytes < msg.payload_bytes:
        raise HTTPException(status_code=400, detail="total_bytes must be >= payload_bytes")

    overhead_bytes = msg.total_bytes - msg.payload_bytes
    now = datetime.now(timezone.utc).isoformat()

    with get_conn() as conn:
        conn.execute(
            """
            INSERT OR IGNORE INTO runs (
              id, created_at, device_id, scenario, transport, tls_enabled,
              connection_mode, payload_bytes, planned_messages, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                msg.run_id, now, msg.device_id, msg.scenario, msg.transport,
                1 if msg.tls_enabled else 0,
                msg.connection_mode, msg.payload_bytes, msg.planned_messages, msg.notes
            ),
        )

        conn.execute(
            """
            INSERT INTO messages (
              run_id, ts, seq, payload_bytes, total_bytes, overhead_bytes,
              latency_ms, energy_mj
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(run_id, seq) DO UPDATE SET
              ts=excluded.ts,
              payload_bytes=excluded.payload_bytes,
              total_bytes=excluded.total_bytes,
              overhead_bytes=excluded.overhead_bytes,
              latency_ms=excluded.latency_ms,
              energy_mj=excluded.energy_mj
            """,
            (
                msg.run_id, now, msg.seq, msg.payload_bytes, msg.total_bytes,
                overhead_bytes, msg.latency_ms, msg.energy_mj
            ),
        )

    return {"status": "stored", "overhead_bytes": overhead_bytes}
