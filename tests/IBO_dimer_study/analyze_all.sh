#!/bin/bash
# Analyze all completed dimer calculations
# Run IBO_distr.py on all .scf.h5 files

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Source environment
source /dodrio/scratch/projects/starting_2025_097/autoCAS4HE_built/autoCAS4HE/setup_hortense.sh

echo "Analyzing all dimer calculations..."
echo ""

for dir in */; do
    element=$(basename "$dir" | sed 's/2$//')
    h5_file="${dir}${element}2_0.scf.h5"

    if [ -f "$h5_file" ]; then
        echo "Analyzing ${element}2..."
        cd "$dir"
        # PYTHONNOUSERSITE=1 ignores ~/.local packages to avoid version conflicts
        python3 /dodrio/scratch/projects/starting_2025_097/autoCAS4HE_built/autoCAS4HE/scripts/IBO_distr.py "${element}2_0.scf.h5" --element "$element" --hpc
        cd ..
    fi
done

echo ""
echo "Analysis complete!"
