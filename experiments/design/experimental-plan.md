# Experimental Plan

## Goal
Quantify the energy cost of secure communication (TLS) on IoT devices by comparing HTTP vs HTTPS and new connections vs keepalive.

## Independent variables
- Security: TLS disabled (HTTP) vs TLS enabled (HTTPS)
- Connection mode: new connection per message vs keepalive

## Dependent variables
- Energy per message (mJ)
- Latency per message (ms)
- Overhead per message (bytes)

## Controlled variables
- Same device and firmware version
- Same WiFi network and similar signal strength
- Same physical placement and distance to router
- Same payload size
- Same backend server and endpoint
- Stable power source

## Scenarios
1. http_no_tls_new
2. http_no_tls_keepalive
3. https_tls_new
4. https_tls_keepalive

## Run definition
A run is a set of N messages sent under the same scenario and configuration.

## Parameters
- Payload size: 256 bytes
- Messages per run (N): 100
- Runs per scenario: 10
- Total messages: 4000

## Procedure per run
1. Generate a unique run_id
2. Send N messages with seq from 1 to N
3. Store energy_mj, latency_ms, payload_bytes, total_bytes
4. Wait a short cooldown interval between runs
5. Repeat until all runs are collected

## Notes
- Prefer multiple independent runs over a single long run to capture variability.
- If instability is observed, increase cooldown time or reduce N temporarily.
