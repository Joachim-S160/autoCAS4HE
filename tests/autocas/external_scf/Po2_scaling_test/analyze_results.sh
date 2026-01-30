#!/bin/bash
# Analyze Po2 scaling test results.
# Reads scaling_results.csv and prints a formatted table.
#
# Usage: ./analyze_results.sh

cd "$(dirname "$0")"

if [ ! -f "scaling_results.csv" ]; then
    echo "No scaling_results.csv found. Run the scaling tests first."
    exit 1
fi

echo "=============================================="
echo "  Po2 Scaling Test Results"
echo "=============================================="
echo ""
printf "%-10s %-10s %-15s %-15s\n" "N_geom" "Status" "Wall_time" "Peak_RSS"
printf "%-10s %-10s %-15s %-15s\n" "------" "------" "---------" "--------"

while IFS=',' read -r n_geom exit_code wall_time peak_rss; do
    if [ "$exit_code" = "0" ]; then
        status="OK"
    else
        status="FAIL($exit_code)"
    fi
    minutes=$((wall_time / 60))
    seconds=$((wall_time % 60))
    mem_mb=$((peak_rss / 1024))
    printf "%-10s %-10s %-15s %-15s\n" "$n_geom" "$status" "${minutes}m ${seconds}s" "${mem_mb} MB"
done < scaling_results.csv

echo ""
echo "Raw data in scaling_results.csv"
echo "Detailed timing in timing_NN.txt files"
