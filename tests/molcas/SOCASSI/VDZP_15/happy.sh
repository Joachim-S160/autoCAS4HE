#!/bin/bash
counter=0
echo "Checking for 'Happy landing' in all *.log files..."
echo ""

for dir in d*/; do
    # Remove trailing slash
    dirname=${dir%/}
    
    # Check all .log files in this directory
    for logfile in "$dir"*.log; do
        # Skip if no .log files exist
        if [ -f "$logfile" ]; then
            # Check if file contains "Happy landing" (case-insensitive)
            if grep -qi "happy landing" "$logfile"; then
                echo "$dirname"
		counter=$((counter + 1))
                break  # Only print dirname once, even if multiple logs contain it
            fi
        fi
    done
done

echo "Total complete autocas jobs: ${counter}"
echo ""
echo "Done!"
