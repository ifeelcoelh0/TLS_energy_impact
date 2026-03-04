import pandas as pd

EXPECTED_SCENARIOS = 4
EXPECTED_RUNS_PER_SCENARIO = 10
EXPECTED_MSGS_PER_RUN = 100

df = pd.read_csv("experiments/analysis/out/messages_with_run.csv")

print("\n--- SANITY CHECK ---")

scenarios = df["scenario"].nunique()
print("Scenarios:", scenarios)

runs = df.groupby("scenario")["run_id"].nunique()
print("Runs per scenario:\n", runs)

msgs = df.groupby("run_id").size()
print("Messages per run (min/max):", msgs.min(), "/", msgs.max())

if scenarios != EXPECTED_SCENARIOS:
    print("❌ Wrong number of scenarios")

if not all(runs == EXPECTED_RUNS_PER_SCENARIO):
    print("❌ Wrong number of runs")

if not all(msgs == EXPECTED_MSGS_PER_RUN):
    print("❌ Wrong number of messages per run")

print("Sanity check complete.")
