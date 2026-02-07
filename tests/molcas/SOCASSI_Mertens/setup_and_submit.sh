#!/bin/bash
# =============================================================================
# Setup and submit SO-CASSI runs for Po2 dissociation curve
# Reproducing Mertens et al. (JPCL 2019, 10, 2879-2884)
# =============================================================================
#
# Usage:
#   ./setup_and_submit.sh          # Set up all 45 geometries (Merlijn's grid)
#   ./setup_and_submit.sh quick    # Set up 10 key geometries for quick test
#   ./setup_and_submit.sh submit   # Submit all prepared runs
#
# Molecule is oriented along z-axis for C2 (XY) symmetry.
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Full set of distances from Merlijn's data (45 points)
ALL_DISTANCES=(
    2.30 2.45 2.50 2.55 2.58 2.61 2.63 2.65 2.66 2.67
    2.68 2.69 2.70 2.71 2.72 2.73 2.74 2.75 2.76 2.77
    2.78 2.79 2.80 2.81 2.83 2.85 2.90 2.95 3.00 3.10
    3.20 3.30 3.40 3.90 4.00 4.25 4.50 4.75 5.00 5.50
    6.00 7.00 8.00 9.00 10.00
)

# Quick test set (10 key points)
QUICK_DISTANCES=(2.50 2.70 2.75 2.80 3.00 3.50 5.00 7.00 10.00)

# Select distance set
if [[ "$1" == "quick" ]]; then
    DISTANCES=("${QUICK_DISTANCES[@]}")
    echo "Using QUICK distance set (${#DISTANCES[@]} points)"
elif [[ "$1" == "submit" ]]; then
    echo "Submitting all prepared runs..."
    for dir in run_*/; do
        if [[ -f "${dir}Po2_so_cassi_mertens.input" ]]; then
            echo "  Submitting ${dir}..."
            (cd "$dir" && qsub job_so_cassi_mertens.pbs)
        fi
    done
    exit 0
else
    DISTANCES=("${ALL_DISTANCES[@]}")
    echo "Using FULL distance set (${#DISTANCES[@]} points)"
fi

echo ""
echo "Creating run directories..."

for i in "${!DISTANCES[@]}"; do
    R=${DISTANCES[$i]}
    RUN_DIR="run_$(printf '%02d' $((i+1)))"
    HALF_R=$(echo "scale=6; $R / 2" | bc)

    echo "  ${RUN_DIR}: R = ${R} A"

    mkdir -p "$RUN_DIR"

    # Create xyz file (z-axis = internuclear axis for C2/XY symmetry)
    cat > "${RUN_DIR}/po2.xyz" << EOF
2
Po2 molecule - ${R} Angstrom bond
Po  0.000000  0.000000  -${HALF_R}
Po  0.000000  0.000000   ${HALF_R}
EOF

    # Copy input and job script
    cp "${SCRIPT_DIR}/Po2_so_cassi_mertens.input" "${RUN_DIR}/"
    cp "${SCRIPT_DIR}/job_so_cassi_mertens.pbs" "${RUN_DIR}/"
done

echo ""
echo "Done! Created ${#DISTANCES[@]} run directories."
echo ""
echo "To submit all runs:  ./setup_and_submit.sh submit"
echo "To extract results:  ./extract_energies.sh"
