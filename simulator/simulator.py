#!/usr/bin/env python3
"""
IoT TLS Energy Simulator
Sends synthetic messages to FastAPI POST /ingest using the project's schema.

Requirements:
  pip install requests

Example:
  python simulator.py --base-url http://127.0.0.1:8000 --runs-per-scenario 3 --messages-per-run 100 --payload-bytes 256
"""

from __future__ import annotations

import argparse
import random
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Tuple

import requests


@dataclass(frozen=True)
class ScenarioSpec:
    scenario: str
    transport: str            # "http" or "https"
    tls_enabled: bool         # True for https_*
    connection_mode: str      # "new" or "keepalive"


SCENARIOS: List[ScenarioSpec] = [
    ScenarioSpec("http_new", "http", False, "new"),
    ScenarioSpec("http_keepalive", "http", False, "keepalive"),
    ScenarioSpec("https_new", "https", True, "new"),
    ScenarioSpec("https_keepalive", "https", True, "keepalive"),
]


def now_stamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def make_run_id(spec: ScenarioSpec, run_index: int, payload_bytes: int, stamp: str) -> str:
    # formato: scenario_runXX_payloadN_YYYYMMDD_HHMMSS
    # exemplo: https_keepalive_run03_256B_20260303_004500
    run_xx = f"run{run_index:02d}"
    return f"{spec.scenario}_{run_xx}_{payload_bytes}B_{stamp}"


def clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def simulate_latency_ms(spec: ScenarioSpec, seq: int, payload_bytes: int, rng: random.Random) -> float:
    """
    Latência artificial:
      base por transporte
      custo adicional no primeiro pacote para "new" (handshake ou setup)
      impacto leve do payload
      jitter aleatório
    """
    base = 18.0 if spec.transport == "http" else 26.0

    # penalização de ligação nova, muito maior em https
    if spec.connection_mode == "new" and seq == 1:
        base += 35.0 if spec.transport == "http" else 95.0

    # impacto do payload
    base += (payload_bytes / 512.0) * (3.0 if spec.transport == "http" else 4.5)

    jitter = rng.normalvariate(0.0, 3.0)
    return clamp(base + jitter, 1.0, 5000.0)


def simulate_energy_mj(spec: ScenarioSpec, seq: int, payload_bytes: int, latency_ms: float, rng: random.Random) -> float:
    """
    Energia artificial (mJ):
      componente fixa por mensagem
      componente proporcional a bytes
      componente proporcional a latência (tempo rádio ligado)
      extra no primeiro pacote para "new", maior em https
    """
    fixed = 0.35 if spec.transport == "http" else 0.50
    per_byte = (0.0012 if spec.transport == "http" else 0.0018) * payload_bytes
    per_latency = (0.0040 if spec.transport == "http" else 0.0048) * latency_ms

    extra = 0.0
    if spec.connection_mode == "new" and seq == 1:
        extra += 1.1 if spec.transport == "http" else 4.2

    noise = rng.normalvariate(0.0, 0.08)
    return clamp(fixed + per_byte + per_latency + extra + noise, 0.01, 10_000.0)


def estimate_total_bytes(spec: ScenarioSpec, payload_bytes: int) -> int:
    """
    Estimativa simples de overhead.
    Não precisa ser precisa agora, apenas consistente.
    """
    # headers e framing base
    overhead = 120 if spec.transport == "http" else 180

    # TLS record overhead aproximado
    if spec.tls_enabled:
        overhead += 60

    # keepalive pode reduzir overhead por requisição
    if spec.connection_mode == "keepalive":
        overhead -= 20

    overhead = max(60, overhead)
    return payload_bytes + overhead


def post_message(session: requests.Session, url: str, payload: Dict, timeout_s: float, retries: int, backoff_s: float) -> Tuple[bool, str]:
    last_err = ""
    for attempt in range(retries + 1):
        try:
            r = session.post(url, json=payload, timeout=timeout_s)
            if 200 <= r.status_code < 300:
                return True, ""
            last_err = f"HTTP {r.status_code}: {r.text[:300]}"
        except Exception as e:
            last_err = str(e)

        if attempt < retries:
            time.sleep(backoff_s * (attempt + 1))

    return False, last_err


def run_simulation(
    base_url: str,
    device_id: str,
    runs_per_scenario: int,
    messages_per_run: int,
    payload_bytes: int,
    seed: int,
    sleep_ms: int,
    timeout_s: float,
    retries: int,
    backoff_s: float,
    dry_run: bool,
) -> None:
    ingest_url = base_url.rstrip("/") + "/ingest"
    rng = random.Random(seed)

    sent = 0
    failed = 0

    with requests.Session() as session:
        for spec in SCENARIOS:
            for run_i in range(1, runs_per_scenario + 1):
                stamp = now_stamp()
                run_id = make_run_id(spec, run_i, payload_bytes, stamp)
                print(f"[RUN] {run_id}")

                for seq in range(1, messages_per_run + 1):
                    latency_ms = simulate_latency_ms(spec, seq, payload_bytes, rng)
                    energy_mj = simulate_energy_mj(spec, seq, payload_bytes, latency_ms, rng)
                    total_bytes = estimate_total_bytes(spec, payload_bytes)

                    msg = {
                        "run_id": run_id,
                        "device_id": device_id,
                        "scenario": spec.scenario,
                        "transport": spec.transport,
                        "tls_enabled": spec.tls_enabled,
                        "connection_mode": spec.connection_mode,
                        "seq": seq,
                        "payload_bytes": payload_bytes,
                        "total_bytes": total_bytes,
                        "latency_ms": round(latency_ms, 3),
                        "energy_mj": round(energy_mj, 6),
                    }

                    if dry_run:
                        print(msg)
                        sent += 1
                    else:
                        ok, err = post_message(
                            session=session,
                            url=ingest_url,
                            payload=msg,
                            timeout_s=timeout_s,
                            retries=retries,
                            backoff_s=backoff_s,
                        )
                        if ok:
                            sent += 1
                        else:
                            failed += 1
                            print(f"[FALHA] run_id={run_id} seq={seq} motivo={err}")

                    if sleep_ms > 0:
                        time.sleep(sleep_ms / 1000.0)

    print(f"\nConcluído. Enviadas={sent} Falhas={failed} Endpoint={ingest_url}")


def main() -> None:
    p = argparse.ArgumentParser(description="Simulador de runs e mensagens para o backend FastAPI /ingest")
    p.add_argument("--base-url", default="http://127.0.0.1:8000", help="Base URL do backend, exemplo http://127.0.0.1:8000")
    p.add_argument("--device-id", default="sim_esp32", help="Identificador do dispositivo")
    p.add_argument("--runs-per-scenario", type=int, default=3, help="Número de runs por cenário")
    p.add_argument("--messages-per-run", type=int, default=100, help="Número de mensagens por run")
    p.add_argument("--payload-bytes", type=int, default=256, help="Payload em bytes, usado no run_id e simulação")
    p.add_argument("--seed", type=int, default=42, help="Seed para reprodutibilidade")
    p.add_argument("--sleep-ms", type=int, default=0, help="Pausa entre mensagens, em ms")
    p.add_argument("--timeout-s", type=float, default=5.0, help="Timeout por POST")
    p.add_argument("--retries", type=int, default=2, help="Número de tentativas extra em caso de falha")
    p.add_argument("--backoff-s", type=float, default=0.3, help="Backoff base entre tentativas")
    p.add_argument("--dry-run", action="store_true", help="Não envia, apenas imprime as mensagens")
    args = p.parse_args()

    run_simulation(
        base_url=args.base_url,
        device_id=args.device_id,
        runs_per_scenario=args.runs_per_scenario,
        messages_per_run=args.messages_per_run,
        payload_bytes=args.payload_bytes,
        seed=args.seed,
        sleep_ms=args.sleep_ms,
        timeout_s=args.timeout_s,
        retries=args.retries,
        backoff_s=args.backoff_s,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()
