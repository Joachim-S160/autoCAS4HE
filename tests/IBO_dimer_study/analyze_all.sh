#!/bin/bash
# Analyze all completed dimer calculations
# Run IBO_distr.py on all .scf.h5 files

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Source environment
source /dodrio/scratch/projects/starting_2025_097/autoCAS4HE_built/autoCAS4HE/setup_hortense.sh

INSTALL_DIR="/dodrio/scratch/projects/starting_2025_097/autoCAS4HE_built/autoCAS4HE"

echo "=============================================="
echo "  IBO Dimer Study - Analysis"
echo "=============================================="
echo ""

# Remove old aggregated files
rm -f IBO_diagnostics.csv

# Count elements
n_analyzed=0
n_total=0

for dir in */; do
    element=$(basename "$dir" | sed 's/2$//')
    h5_file="${dir}${element}2_0.scf.h5"
    n_total=$((n_total + 1))

    if [ -f "$h5_file" ]; then
        echo "Analyzing ${element}2..."
        cd "$dir"
        # Remove old CSV to avoid duplicates
        rm -f IBO_diagnostics.csv
        python3 ${INSTALL_DIR}/scripts/IBO_distr.py "${element}2_0.scf.h5" --element "$element" --hpc
        cd ..
        n_analyzed=$((n_analyzed + 1))
    else
        echo "Skipping ${element}2 (no .scf.h5 file)"
    fi
done

echo ""
echo "=============================================="
echo "  Aggregating diagnostic data..."
echo "=============================================="

# Aggregate all CSV files into one master CSV
first=true
for csv in */IBO_diagnostics.csv; do
    if [ -f "$csv" ]; then
        if $first; then
            # Include header from first file
            cat "$csv" >> IBO_diagnostics.csv
            first=false
        else
            # Skip header for subsequent files
            tail -n +2 "$csv" >> IBO_diagnostics.csv
        fi
    fi
done

if [ -f "IBO_diagnostics.csv" ]; then
    echo "Aggregated diagnostics saved to: IBO_diagnostics.csv"

    # Count failures
    n_fail=$(grep -c "True" IBO_diagnostics.csv 2>/dev/null || echo "0")
    n_ok=$(grep -c "False" IBO_diagnostics.csv 2>/dev/null || echo "0")

    echo ""
    echo "Results summary:"
    echo "  - Analyzed: $n_analyzed / $n_total elements"
    echo "  - IBO OK:   $n_ok elements"
    echo "  - IBO FAIL: $n_fail elements"
fi

echo ""
echo "=============================================="
echo "  Creating animations (GIF + MP4)..."
echo "=============================================="

python3 ${INSTALL_DIR}/scripts/create_IBO_gif.py --input-dir . --output IBO_all_elements --duration 500

echo ""
echo "=============================================="
echo "  Analysis complete!"
echo "=============================================="
echo ""
echo "Output files:"
echo "  - IBO_diagnostics.csv      (all diagnostic data)"
echo "  - IBO_all_elements.gif     (animated overview)"
echo "  - IBO_all_elements.mp4     (video - easier to pause in VSCode)"
echo "  - */\*_IBO_distribution.pdf (individual plots)"
echo "  - */\*_IBO_distribution.png (individual plots)"
echo ""
