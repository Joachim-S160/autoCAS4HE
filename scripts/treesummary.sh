#!/bin/bash
# treesummary.sh - Generate tree structure summary of test output directories
# Usage: treesummary.sh -o <output_file> -i <path1> [path2] [path3] ...

usage() {
    echo "Usage: $0 -o <output_file> -i <path1> [path2] [path3] ..."
    echo ""
    echo "Options:"
    echo "  -o <file>    Output file for the summary"
    echo "  -i <paths>   One or more paths to summarize (remaining arguments)"
    echo "  -h           Show this help message"
    echo ""
    echo "Example:"
    echo "  $0 -o summary.txt -i tests/serenity/Po2_RHF_benchmark tests/molcas/Po2_RHF_benchmark"
    exit 1
}

# Parse arguments
OUTPUT_FILE=""
PATHS=()

while [[ $# -gt 0 ]]; do
    case $1 in
        -o)
            OUTPUT_FILE="$2"
            shift 2
            ;;
        -i)
            shift
            # Collect all remaining arguments as paths
            while [[ $# -gt 0 && ! "$1" =~ ^- ]]; do
                PATHS+=("$1")
                shift
            done
            ;;
        -h|--help)
            usage
            ;;
        *)
            echo "Unknown option: $1"
            usage
            ;;
    esac
done

# Validate arguments
if [[ -z "$OUTPUT_FILE" ]]; then
    echo "Error: Output file (-o) is required"
    usage
fi

if [[ ${#PATHS[@]} -eq 0 ]]; then
    echo "Error: At least one input path (-i) is required"
    usage
fi

# Generate summary
{
    echo "# Tree Summary"
    echo "Generated: $(date)"
    echo "Host: $(hostname)"
    echo ""

    for path in "${PATHS[@]}"; do
        echo "========================================"
        echo "## Directory: $path"
        echo "========================================"

        if [[ ! -d "$path" ]]; then
            echo "ERROR: Directory does not exist"
            echo ""
            continue
        fi

        echo ""
        echo "### Tree Structure"
        echo '```'
        if command -v tree &> /dev/null; then
            tree -h --du "$path" 2>/dev/null || tree "$path"
        else
            # Fallback if tree is not available
            find "$path" -type f -exec ls -lh {} \; | awk '{print $5, $9}'
        fi
        echo '```'
        echo ""

        echo "### File Sizes"
        echo '```'
        du -sh "$path"/* 2>/dev/null | sort -h
        echo '```'
        echo ""

        echo "### Key Output Files"
        echo '```'
        # Look for common output files
        for pattern in "*.log" "*.out" "*.err" "*.dat" "energies*" "*energy*" "*.pdf"; do
            files=$(find "$path" -name "$pattern" -type f 2>/dev/null)
            if [[ -n "$files" ]]; then
                echo "--- $pattern ---"
                echo "$files"
            fi
        done
        echo '```'
        echo ""

        # Show last 50 lines of any .log or .out files
        echo "### Log File Excerpts (last 50 lines)"
        for logfile in $(find "$path" -name "*.log" -o -name "*.out" 2>/dev/null | head -5); do
            if [[ -f "$logfile" && -s "$logfile" ]]; then
                echo ""
                echo "#### $logfile"
                echo '```'
                tail -50 "$logfile"
                echo '```'
            fi
        done
        echo ""

    done

} > "$OUTPUT_FILE"

echo "Summary written to: $OUTPUT_FILE"
echo "Directories summarized: ${#PATHS[@]}"
