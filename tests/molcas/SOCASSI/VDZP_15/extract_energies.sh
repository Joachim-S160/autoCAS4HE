#!/bin/bash

# Extract SO-CASSI energies from run_*/ directories
# Distance is extracted from po2.xyz comment line (e.g., "Po2 molecule - 2.10 Angstrom bond")

OUTPUT_FILE="so_cassi_energies.dat"
echo "Extracting SO-CASSI energies..."
> "$OUTPUT_FILE"

for dir in run_*/; do
    log=$(ls ${dir}*.o* 2>/dev/null | head -n 1)
    xyz="${dir}po2.xyz"

    if [[ -f "$log" && -f "$xyz" ]]; then
        # Extract distance from xyz comment line (line 2)
        dist=$(sed -n '2p' "$xyz" | grep -oP '[\d.]+(?=\s*Angstrom)')

        # Extract lowest RASSI State energy (first occurrence only)
        energy=$(grep "::    RASSI State    1     Total energy:" "$log" | head -n 1 | awk '{print $NF}')

        if [[ -n "$energy" && -n "$dist" ]]; then
            echo -e "${dist}\t${energy}"
        else
            echo "Warning: Missing data for ${dir} (dist=$dist, energy=$energy)" >&2
        fi
    fi
done | sort -n >> "$OUTPUT_FILE"

n_entries=$(wc -l < "$OUTPUT_FILE")
echo "Extracted $n_entries energies to: $OUTPUT_FILE"
echo ""
echo "=== Preview ==="
head -n 5 "$OUTPUT_FILE"
echo ""
echo "Done!"
