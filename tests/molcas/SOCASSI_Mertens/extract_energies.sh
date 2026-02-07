#!/bin/bash
# =============================================================================
# Extract CASSCF, CASPT2, and SO-CASSI energies from Mertens reproduction runs
# =============================================================================

echo "=============================================="
echo "  Extracting energies from Mertens SO-CASSI"
echo "=============================================="

# Output files
CASSCF_FILE="casscf_energies.dat"
CASPT2_FILE="caspt2_energies.dat"
RASSI_FILE="sorassi_energies.dat"
RASSI_STATES_FILE="sorassi_10states.dat"
CHARGE_FILE="charge_check.dat"

# Initialize with headers
echo "# CASSCF Singlet Root 1 (irrep 1) energies (Hartree)" > "$CASSCF_FILE"
echo "# Distance(A)  Energy(Ha)" >> "$CASSCF_FILE"

echo "# CASPT2 Singlet Root 1 (irrep 1) energies (Hartree)" > "$CASPT2_FILE"
echo "# Distance(A)  Energy(Ha)" >> "$CASPT2_FILE"

echo "# SO-CASSI State 1 energies (Hartree)" > "$RASSI_FILE"
echo "# Distance(A)  Energy(Ha)" >> "$RASSI_FILE"

echo "# SO-CASSI States 1-10 energies (Hartree)" > "$RASSI_STATES_FILE"
echo "# Distance(A)  S1  S2  S3  S4  S5  S6  S7  S8  S9  S10" >> "$RASSI_STATES_FILE"

echo "# Charge check: verify neutral Po2 (should be 0.00)" > "$CHARGE_FILE"
echo "# Distance(A)  Charge  Electrons" >> "$CHARGE_FILE"

for dir in run_*/; do
    log=$(ls ${dir}*.o* 2>/dev/null | head -n 1)

    if [[ -f "$log" ]]; then
        # Extract distance from xyz file
        xyz="${dir}po2.xyz"
        if [[ -f "$xyz" ]]; then
            # Get z-coordinate of second atom and multiply by 2
            z_coord=$(awk 'NR==4 {print $4}' "$xyz")
            dist=$(echo "scale=2; $z_coord * 2" | bc)
        else
            echo "Warning: No xyz file for ${dir}" >&2
            continue
        fi

        # Check charge (should be 0.00 for neutral Po2)
        charge=$(grep "Total molecular charge" "$log" | head -1 | awk '{print $NF}')
        electrons=$(grep "Total electronic charge=" "$log" | head -1 | sed 's/.*=//;s/ .*//')

        # Extract CASSCF Root 1 energy (first RASSCF = singlet irrep 1)
        casscf=$(grep "RASSCF root number  1 Total energy:" "$log" | head -n 1 | awk '{print $NF}')

        # Extract CASPT2 Root 1 energy (first CASPT2 = singlet irrep 1)
        caspt2=$(grep "CASPT2 Root  1     Total energy:" "$log" | head -n 1 | awk '{print $NF}')

        # Extract SO-RASSI State 1 energy
        rassi1=$(grep "RASSI State    1     Total energy:" "$log" | head -n 1 | awk '{print $NF}')

        # Extract SO-RASSI States 1-10
        rassi_states=""
        for s in $(seq 1 10); do
            if [[ $s -lt 10 ]]; then
                pattern="RASSI State    ${s}     Total energy:"
            else
                pattern="RASSI State   ${s}     Total energy:"
            fi
            state_e=$(grep "$pattern" "$log" | head -n 1 | awk '{print $NF}')
            rassi_states="${rassi_states}\t${state_e}"
        done

        # Write to files
        [[ -n "$casscf" ]] && echo -e "${dist}\t${casscf}" >> "$CASSCF_FILE"
        [[ -n "$caspt2" ]] && echo -e "${dist}\t${caspt2}" >> "$CASPT2_FILE"
        [[ -n "$rassi1" ]] && echo -e "${dist}\t${rassi1}" >> "$RASSI_FILE"
        [[ -n "$rassi_states" ]] && echo -e "${dist}${rassi_states}" >> "$RASSI_STATES_FILE"
        [[ -n "$charge" ]] && echo -e "${dist}\t${charge}\t${electrons}" >> "$CHARGE_FILE"

        echo "Processed ${dir}: dist=${dist}A, charge=${charge}, CASSCF=${casscf}, SO-RASSI=${rassi1}"
    else
        echo "Warning: No log file for ${dir}" >&2
    fi
done

# Sort all files by distance
for f in "$CASSCF_FILE" "$CASPT2_FILE" "$RASSI_FILE" "$RASSI_STATES_FILE" "$CHARGE_FILE"; do
    head -2 "$f" > "${f}.tmp"
    tail -n +3 "$f" | sort -n >> "${f}.tmp"
    mv "${f}.tmp" "$f"
done

echo ""
echo "=============================================="
echo "  Summary"
echo "=============================================="
echo "CASSCF energies:      $CASSCF_FILE ($(grep -c '^[0-9]' "$CASSCF_FILE") points)"
echo "CASPT2 energies:      $CASPT2_FILE ($(grep -c '^[0-9]' "$CASPT2_FILE") points)"
echo "SO-CASSI State 1:     $RASSI_FILE ($(grep -c '^[0-9]' "$RASSI_FILE") points)"
echo "SO-CASSI States 1-10: $RASSI_STATES_FILE ($(grep -c '^[0-9]' "$RASSI_STATES_FILE") points)"
echo ""

# Quick dissociation energy estimate
if [[ $(grep -c '^[0-9]' "$RASSI_FILE") -ge 2 ]]; then
    E_eq=$(sort -t$'\t' -k2,2 -g "$RASSI_FILE" | grep '^[0-9]' | head -1)
    E_dis=$(grep '^[0-9]' "$RASSI_FILE" | sort -n | tail -1)
    R_eq=$(echo "$E_eq" | awk '{print $1}')
    E_eq_val=$(echo "$E_eq" | awk '{print $2}')
    R_dis=$(echo "$E_dis" | awk '{print $1}')
    E_dis_val=$(echo "$E_dis" | awk '{print $2}')
    D_e=$(echo "scale=6; ($E_dis_val - ($E_eq_val)) * 27.2114" | bc 2>/dev/null)
    echo "=== Quick D_e estimate ==="
    echo "  E_min at R=${R_eq} A: ${E_eq_val} Ha"
    echo "  E_dis at R=${R_dis} A: ${E_dis_val} Ha"
    echo "  D_e = ${D_e} eV (target: ~1.84 eV)"
fi

echo ""
echo "=== Charge check ==="
cat "$CHARGE_FILE"
echo ""
echo "Done!"
