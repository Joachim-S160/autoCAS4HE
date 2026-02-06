#!/bin/bash

# Extract CASSCF, CASPT2, and SO-CASSI energies from run_*/ directories
# Distance is extracted from the log file Cartesian coordinates

echo "=============================================="
echo "  Extracting all energies from SO-CASSI runs"
echo "=============================================="

# Output files
CASSCF_FILE="casscf_energies.dat"
CASPT2_FILE="caspt2_energies.dat"
RASSI_FILE="rassi_energies.dat"
RASSI_STATES_FILE="rassi_10states.dat"

# Initialize files with headers
echo "# CASSCF Root 1 energies (Hartree)" > "$CASSCF_FILE"
echo "# Distance(A)  Energy(Ha)" >> "$CASSCF_FILE"

echo "# CASPT2 Root 1 energies (Hartree)" > "$CASPT2_FILE"
echo "# Distance(A)  Energy(Ha)" >> "$CASPT2_FILE"

echo "# SO-CASSI State 1 energies (Hartree)" > "$RASSI_FILE"
echo "# Distance(A)  Energy(Ha)" >> "$RASSI_FILE"

echo "# SO-CASSI States 1-10 energies (Hartree)" > "$RASSI_STATES_FILE"
echo "# Distance(A)  State1  State2  State3  State4  State5  State6  State7  State8  State9  State10" >> "$RASSI_STATES_FILE"

for dir in run_*/; do
    # Find the output file (PBS output)
    log=$(ls ${dir}*.o* 2>/dev/null | head -n 1)

    if [[ -f "$log" ]]; then
        # Extract distance from Cartesian coordinates in log file
        # Po2 coordinates: PO1 at -x, PO2 at +x, so distance = 2*x
        x_coord=$(grep -A 4 "Cartesian coordinates in angstrom:" "$log" | grep "PO1" | head -1 | awk '{print $3}')
        if [[ -n "$x_coord" ]]; then
            # Remove minus sign and multiply by 2
            x_abs=${x_coord#-}
            dist=$(echo "scale=2; $x_abs * 2" | bc)
        else
            echo "Warning: Could not extract distance for ${dir}" >&2
            continue
        fi

        # Extract CASSCF Root 1 energy (first occurrence)
        casscf=$(grep "RASSCF root number  1 Total energy:" "$log" | head -n 1 | awk '{print $NF}')

        # Extract CASPT2 Root 1 energy (first occurrence)
        caspt2=$(grep "CASPT2 Root  1     Total energy:" "$log" | head -n 1 | awk '{print $NF}')

        # Extract RASSI State 1 energy
        rassi1=$(grep "RASSI State    1     Total energy:" "$log" | head -n 1 | awk '{print $NF}')

        # Extract RASSI States 1-10
        rassi_states=""
        for i in $(seq 1 10); do
            # Handle spacing for single vs double digit state numbers
            if [[ $i -lt 10 ]]; then
                pattern="RASSI State    ${i}     Total energy:"
            else
                pattern="RASSI State   ${i}     Total energy:"
            fi
            state_e=$(grep "$pattern" "$log" | head -n 1 | awk '{print $NF}')
            rassi_states="${rassi_states}\t${state_e}"
        done

        # Write to files
        [[ -n "$casscf" ]] && echo -e "${dist}\t${casscf}" >> "$CASSCF_FILE"
        [[ -n "$caspt2" ]] && echo -e "${dist}\t${caspt2}" >> "$CASPT2_FILE"
        [[ -n "$rassi1" ]] && echo -e "${dist}\t${rassi1}" >> "$RASSI_FILE"
        [[ -n "$rassi_states" ]] && echo -e "${dist}${rassi_states}" >> "$RASSI_STATES_FILE"

        echo "Processed ${dir}: dist=${dist}A, CASSCF=${casscf}, CASPT2=${caspt2}, RASSI1=${rassi1}"
    else
        echo "Warning: No log file found for ${dir}" >&2
    fi
done

# Sort all files by distance
for f in "$CASSCF_FILE" "$CASPT2_FILE" "$RASSI_FILE" "$RASSI_STATES_FILE"; do
    # Preserve header, sort the rest
    head -2 "$f" > "${f}.tmp"
    tail -n +3 "$f" | sort -n >> "${f}.tmp"
    mv "${f}.tmp" "$f"
done

echo ""
echo "=============================================="
echo "  Summary"
echo "=============================================="
echo "CASSCF energies:     $CASSCF_FILE ($(grep -c '^[0-9]' "$CASSCF_FILE") points)"
echo "CASPT2 energies:     $CASPT2_FILE ($(grep -c '^[0-9]' "$CASPT2_FILE") points)"
echo "SO-CASSI State 1:    $RASSI_FILE ($(grep -c '^[0-9]' "$RASSI_FILE") points)"
echo "SO-CASSI States 1-10: $RASSI_STATES_FILE ($(grep -c '^[0-9]' "$RASSI_STATES_FILE") points)"
echo ""
echo "=== CASSCF Preview ==="
head -5 "$CASSCF_FILE"
echo ""
echo "=== CASPT2 Preview ==="
head -5 "$CASPT2_FILE"
echo ""
echo "=== SO-CASSI State 1 Preview ==="
head -5 "$RASSI_FILE"
echo ""
echo "Done!"
