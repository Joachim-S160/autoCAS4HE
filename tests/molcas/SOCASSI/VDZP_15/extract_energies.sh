#!/bin/bash

# Extract SO-CASSI energies for s28t70q50 (old simulations in t70/ folder)
echo "Extracting s28t70q50 energies..."
> s28t70q50_energies.dat

for log in t70/d*_Po2_example.log; do
    # Extract distance from filename (e.g., d300 -> 3.00)
    dist=$(basename "$log" | grep -oP 'd\K[0-9]+')
    dist_formatted=$(awk "BEGIN {printf \"%.2f\", $dist/100}")
    
    # Extract lowest RASSI State energy (first occurrence only)
    energy=$(grep "::    RASSI State    1     Total energy:" "$log" | head -n 1 | awk '{print $NF}')
    
    if [[ -n "$energy" ]]; then
        echo -e "${dist_formatted}\t${energy}"
    fi
done | sort -n >> s28t70q50_energies.dat

echo "s28t70q50 energies saved to: s28t70q50_energies.dat"
echo ""

# Extract SO-CASSI energies for s28t90q50 (current simulations in d*/ folders)
echo "Extracting s28t90q50 energies..."
> s28t90q50_energies.dat

for dir in d*/; do
    log="${dir}Po2_example.log"
    
    if [[ -f "$log" ]]; then
        # Extract distance from directory name (e.g., d300 -> 3.00)
        dist=$(echo "$dir" | grep -oP 'd\K[0-9]+')
        dist_formatted=$(awk "BEGIN {printf \"%.2f\", $dist/100}")
        
        # Extract lowest RASSI State energy (first occurrence only)
        energy=$(grep "::    RASSI State    1     Total energy:" "$log" | head -n 1 | awk '{print $NF}')
        
        if [[ -n "$energy" ]]; then
            echo -e "${dist_formatted}\t${energy}"
        fi
    fi
done | sort -n >> s28t90q50_energies.dat

echo "s28t90q50 energies saved to: s28t90q50_energies.dat"
echo ""
echo "Done! Preview of files:"
echo ""
echo "=== s28t70q50_energies.dat ==="
head -n 5 s28t70q50_energies.dat
echo ""
echo "=== s28t90q50_energies.dat ==="
head -n 5 s28t90q50_energies.dat
