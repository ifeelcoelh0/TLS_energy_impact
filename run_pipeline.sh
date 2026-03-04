#!/bin/bash
set -e

echo "Running simulator..."
python simulator/simulator.py --runs-per-scenario 10 --messages-per-run 100 --payload-bytes 256

echo "Exporting CSV..."
python experiments/analysis/export_csv.py

echo "Sanity check..."
python experiments/analysis/sanity_check.py

echo "Generating plots..."
python experiments/analysis/generate_plots_run_level.py

echo "Done."
