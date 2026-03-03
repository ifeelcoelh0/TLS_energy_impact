# Run Checklist

## Before starting
- Backend running and reachable
- SQLite file exists and is writable
- Correct scenario name selected
- Payload size confirmed
- Device connected to the intended WiFi network
- Power source fixed (same powerbank or supply)
- Device position and distance to router unchanged

## During each run
- Use a unique run_id
- Send messages with seq from 1 to N (no repeats)
- Log any anomalies (timeouts, retries, disconnects)

## After each run
- Confirm messages_count == N via /runs/{run_id}
- Record any notes about network conditions
- Wait cooldown interval before next run

## After each scenario
- Confirm number of runs collected
- Quick sanity check: energy and latency ranges look plausible
