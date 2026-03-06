#!/bin/bash
set -e


echo "Exporting CSV..."
python experiments/analysis/export_csv.py

echo "Sanity check..."
python experiments/analysis/sanity_check.py

echo "Generating plots..."
python experiments/analysis/generate_plots_run_level.py

echo "Done."
