import json
import sqlite3
from datetime import datetime

import paho.mqtt.client as mqtt

BROKER = "192.168.68.130"
PORT = 1883
TOPIC = "tls_energy/#"

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "backend" / "data" / "experiments.sqlite"
SCHEMA_PATH = BASE_DIR / "backend" / "app" / "db" / "schema.sql"


# -------- DB --------

def init_db():
    conn = sqlite3.connect(DB_PATH)

    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        conn.executescript(f.read())

    conn.commit()
    conn.close()

    print("Database initialized")


def get_conn():
    return sqlite3.connect(DB_PATH)


def insert_run(run_id, scenario):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        INSERT OR IGNORE INTO runs (
            id, created_at, device_id, scenario,
            transport, tls_enabled, connection_mode,
            payload_bytes, planned_messages, notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        run_id,
        datetime.utcnow().isoformat(),
        "ESP32",
        scenario,
        "mqtt",
        0,  # sem TLS neste cenário
        "keepalive",
        0,  # opcional
        100,
        "mqtt experiment"
    ))

    conn.commit()
    conn.close()


def insert_message(data, total_bytes):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO messages (
            run_id, ts, seq, payload_bytes,
            total_bytes, overhead_bytes,
            latency_ms, energy_mj
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data["run_id"],
        datetime.utcnow().isoformat(),
        data["msg_id"],
        data["payload_size"],
        total_bytes,
        total_bytes - data["payload_size"],
        0,  # MQTT não mede latency aqui
        0   # energia calculas depois
    ))

    conn.commit()
    conn.close()


# -------- MQTT --------
def on_connect(client, userdata, flags, reason_code, properties=None):
    print(f"[CONNECTED] {reason_code}")
    client.subscribe(TOPIC)


def on_message(client, userdata, msg):
    try:
        payload_str = msg.payload.decode()
        data = json.loads(payload_str)

        run_id = data["run_id"]
        scenario = data["scenario"]

        # tamanho total (aproximação)
        total_bytes = len(msg.payload)

        # 🔥 garantir run existe
        insert_run(run_id, scenario)

        # 🔥 inserir mensagem
        insert_message(data, total_bytes)

        print(f"[OK] run={run_id} msg={data['msg_id']} bytes={total_bytes}")

    except Exception as e:
        print(f"[ERROR] {e}")


def main():
    init_db()

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(BROKER, PORT, 60)
    client.loop_forever()


if __name__ == "__main__":
    main()
