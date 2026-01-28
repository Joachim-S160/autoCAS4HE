#!/bin/bash
# Analyze all completed dimer calculations
# Run IBO_distr.py on all .scf.h5 files

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Source environment
source ~/autoCAS4HE/setup_autocas_env.sh

echo "Analyzing all dimer calculations..."
echo ""

for dir in */; do
    element=$(basename "$dir" | sed 's/2$//')
    h5_file="${dir}${element}2_0.scf.h5"

    if [ -f "$h5_file" ]; then
        echo "Analyzing ${element}2..."
        cd "$dir"
        python3 ~/autoCAS4HE/scripts/IBO_distr.py "${element}2_0.scf.h5" --element "$element"
        cd ..
    fi
done

echo ""
echo "Analysis complete!"
