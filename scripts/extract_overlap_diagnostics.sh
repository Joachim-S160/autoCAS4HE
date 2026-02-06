#!/bin/bash
# extract_overlap_diagnostics.sh
# Extracts overlap matrix diagnostics (S1, S2, EQ1, EQ2) from autoCAS log files
# Usage: ./extract_overlap_diagnostics.sh <log_file_or_directory> [output_csv]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

usage() {
    echo "Usage: $0 <log_file_or_directory> [output_csv]"
    echo ""
    echo "Arguments:"
    echo "  log_file_or_directory  Single log file or directory containing logs"
    echo "  output_csv             Output CSV file (default: diagnostics_extracted.csv)"
    echo ""
    echo "Examples:"
    echo "  $0 autocas_output.log"
    echo "  $0 /path/to/VDZP/"
    echo "  $0 /path/to/Po2_overlap_diagnostics/ all_diagnostics.csv"
    exit 1
}

# Check arguments
if [ $# -lt 1 ]; then
    usage
fi

INPUT="$1"
OUTPUT="${2:-diagnostics_extracted.csv}"

# Function to extract diagnostics from a single log file
extract_from_log() {
    local logfile="$1"
    local basename=$(basename "$logfile")
    local dirname=$(dirname "$logfile")

    # Try to extract basis and geometry info from path
    local basis=""
    local geom_id=""

    # Check path for basis set
    if [[ "$dirname" == *"VDZP"* ]]; then
        basis="VDZP"
    elif [[ "$dirname" == *"VTZP"* ]]; then
        basis="VTZP"
    elif [[ "$dirname" == *"VQZP"* ]]; then
        basis="VQZP"
    else
        basis="unknown"
    fi

    # Try to extract geometry ID from filename or path
    if [[ "$basename" =~ po2_([0-9]+) ]]; then
        geom_id="${BASH_REMATCH[1]}"
    elif [[ "$dirname" =~ geom_?([0-9]+) ]]; then
        geom_id="${BASH_REMATCH[1]}"
    else
        geom_id="0"
    fi

    # Initialize variables
    local s1_basis_funcs="" s1_min_eig="" s1_max_eig="" s1_cond="" s1_lt_1e6="" s1_lt_1e8="" s1_lt_1e10=""
    local s2_minao_funcs="" s2_min_eig="" s2_max_eig="" s2_cond="" s2_lt_1e6="" s2_lt_1e8=""
    local eq1_size="" eq1_min_eig="" eq1_max_eig="" eq1_cond=""
    local eq2_size="" eq2_min_eig="" eq2_max_eig="" eq2_cond=""
    local ibo_cycles=""

    # Extract S1 (AO Overlap) diagnostics
    local s1_block=$(grep -A 10 "=== AO Overlap Matrix (S1) Diagnostics ===" "$logfile" 2>/dev/null | head -10)
    if [ -n "$s1_block" ]; then
        s1_basis_funcs=$(echo "$s1_block" | grep "Basis functions:" | awk '{print $NF}')
        s1_min_eig=$(echo "$s1_block" | grep "Min eigenvalue:" | awk '{print $NF}')
        s1_max_eig=$(echo "$s1_block" | grep "Max eigenvalue:" | awk '{print $NF}')
        s1_cond=$(echo "$s1_block" | grep "Condition number:" | awk '{print $NF}')
        s1_lt_1e6=$(echo "$s1_block" | grep "Eigenvalues < 1e-6:" | awk '{print $NF}')
        s1_lt_1e8=$(echo "$s1_block" | grep "Eigenvalues < 1e-8:" | awk '{print $NF}')
        s1_lt_1e10=$(echo "$s1_block" | grep "Eigenvalues < 1e-10:" | awk '{print $NF}')
    fi

    # Extract S2 (MINAO Overlap) diagnostics
    local s2_block=$(grep -A 8 "=== MINAO Overlap Matrix (S2) Diagnostics ===" "$logfile" 2>/dev/null | head -8)
    if [ -n "$s2_block" ]; then
        s2_minao_funcs=$(echo "$s2_block" | grep "MINAO functions:" | awk '{print $NF}')
        s2_min_eig=$(echo "$s2_block" | grep "Min eigenvalue:" | awk '{print $NF}')
        s2_max_eig=$(echo "$s2_block" | grep "Max eigenvalue:" | awk '{print $NF}')
        s2_cond=$(echo "$s2_block" | grep "Condition number:" | awk '{print $NF}')
        s2_lt_1e6=$(echo "$s2_block" | grep "Eigenvalues < 1e-6:" | awk '{print $NF}')
        s2_lt_1e8=$(echo "$s2_block" | grep "Eigenvalues < 1e-8:" | awk '{print $NF}')
    fi

    # Extract EQ1 diagnostics
    local eq1_block=$(grep -A 6 "=== IAO EQ1 Orthogonalization Diagnostics ===" "$logfile" 2>/dev/null | head -6)
    if [ -n "$eq1_block" ]; then
        eq1_size=$(echo "$eq1_block" | grep "Matrix size:" | awk '{print $3}')
        eq1_min_eig=$(echo "$eq1_block" | grep "Min eigenvalue:" | awk '{print $NF}')
        eq1_max_eig=$(echo "$eq1_block" | grep "Max eigenvalue:" | awk '{print $NF}')
        eq1_cond=$(echo "$eq1_block" | grep "Condition number:" | awk '{print $NF}')
    fi

    # Extract EQ2 (othoA) diagnostics
    local eq2_block=$(grep -A 6 "=== IAO EQ2 (othoA) Orthogonalization Diagnostics ===" "$logfile" 2>/dev/null | head -6)
    if [ -n "$eq2_block" ]; then
        eq2_size=$(echo "$eq2_block" | grep "Matrix size:" | awk '{print $3}')
        eq2_min_eig=$(echo "$eq2_block" | grep "Min eigenvalue:" | awk '{print $NF}')
        eq2_max_eig=$(echo "$eq2_block" | grep "Max eigenvalue:" | awk '{print $NF}')
        eq2_cond=$(echo "$eq2_block" | grep "Condition number:" | awk '{print $NF}')
    fi

    # Extract IBO convergence info
    ibo_cycles=$(grep -o "Converged after [0-9]* orbital rotation cycles" "$logfile" 2>/dev/null | tail -1 | awk '{print $3}')

    # Only output if we found any diagnostics
    if [ -n "$s1_min_eig" ] || [ -n "$s2_min_eig" ] || [ -n "$eq1_min_eig" ] || [ -n "$eq2_min_eig" ]; then
        echo "$basis,$geom_id,$s1_basis_funcs,$s1_min_eig,$s1_max_eig,$s1_cond,$s1_lt_1e6,$s1_lt_1e8,$s1_lt_1e10,$s2_minao_funcs,$s2_min_eig,$s2_max_eig,$s2_cond,$s2_lt_1e6,$s2_lt_1e8,$eq1_size,$eq1_min_eig,$eq1_max_eig,$eq1_cond,$eq2_size,$eq2_min_eig,$eq2_max_eig,$eq2_cond,$ibo_cycles,$logfile"
        return 0
    else
        return 1
    fi
}

# Main logic
echo -e "${GREEN}Overlap Diagnostics Extractor${NC}"
echo "================================"
echo ""

# Write CSV header
echo "basis,geom_id,S1_basis_funcs,S1_min_eig,S1_max_eig,S1_cond,S1_lt_1e-6,S1_lt_1e-8,S1_lt_1e-10,S2_minao_funcs,S2_min_eig,S2_max_eig,S2_cond,S2_lt_1e-6,S2_lt_1e-8,EQ1_size,EQ1_min_eig,EQ1_max_eig,EQ1_cond,EQ2_size,EQ2_min_eig,EQ2_max_eig,EQ2_cond,IBO_cycles,source_file" > "$OUTPUT"

found=0
processed=0

if [ -f "$INPUT" ]; then
    # Single file
    echo -e "Processing single file: ${YELLOW}$INPUT${NC}"
    processed=1
    if extract_from_log "$INPUT" >> "$OUTPUT" 2>/dev/null; then
        found=1
    fi
elif [ -d "$INPUT" ]; then
    # Directory - search recursively for log files
    echo -e "Searching directory: ${YELLOW}$INPUT${NC}"
    echo ""

    # Find all potential log files
    while IFS= read -r logfile; do
        processed=$((processed + 1))
        if extract_from_log "$logfile" >> "$OUTPUT" 2>/dev/null; then
            found=$((found + 1))
            echo -e "  ${GREEN}[OK]${NC} $logfile"
        fi
    done < <(find "$INPUT" -type f \( -name "autocas_output.log" -o -name "*.log" -o -name "*.o[0-9]*" \) 2>/dev/null)
else
    echo -e "${RED}Error: $INPUT is neither a file nor a directory${NC}"
    exit 1
fi

echo ""
echo "================================"
echo -e "Processed: ${YELLOW}$processed${NC} files"
echo -e "Found diagnostics in: ${GREEN}$found${NC} files"
echo -e "Output saved to: ${GREEN}$OUTPUT${NC}"
echo ""

# Show summary if we have data
if [ $found -gt 0 ]; then
    echo "Quick Summary:"
    echo "--------------"
    # Show unique basis sets and count
    tail -n +2 "$OUTPUT" | cut -d',' -f1 | sort | uniq -c | while read count basis; do
        echo "  $basis: $count entries"
    done
    echo ""

    # Show min eigenvalue ranges
    echo "S1 (AO Overlap) min eigenvalue range:"
    tail -n +2 "$OUTPUT" | cut -d',' -f4 | sort -g | head -1 | xargs -I{} echo "  Min: {}"
    tail -n +2 "$OUTPUT" | cut -d',' -f4 | sort -g | tail -1 | xargs -I{} echo "  Max: {}"
    echo ""

    echo "S2 (MINAO Overlap) min eigenvalue range:"
    tail -n +2 "$OUTPUT" | cut -d',' -f11 | sort -g | head -1 | xargs -I{} echo "  Min: {}"
    tail -n +2 "$OUTPUT" | cut -d',' -f11 | sort -g | tail -1 | xargs -I{} echo "  Max: {}"
    echo ""

    echo "EQ2 (othoA) condition number range:"
    tail -n +2 "$OUTPUT" | cut -d',' -f23 | sort -g | head -1 | xargs -I{} echo "  Min: {}"
    tail -n +2 "$OUTPUT" | cut -d',' -f23 | sort -g | tail -1 | xargs -I{} echo "  Max: {}"
fi
