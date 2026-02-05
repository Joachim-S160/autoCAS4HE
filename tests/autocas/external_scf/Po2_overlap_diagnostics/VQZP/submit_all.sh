#!/bin/bash
# Master script: Submit all SCF jobs in parallel, then autoCAS with dependency
# Usage: ./submit_all.sh

set -e

GEOM_IDS="000 003 005 007 009 011 013 015 017 019"
SCF_JOB_IDS=""

echo "=============================================="
echo "  Po2 Overlap Diagnostics - VQZP"
echo "=============================================="
echo "Submitting 10 parallel SCF jobs..."
echo ""

for ID in $GEOM_IDS; do
    if [ -f "po2_${ID}.scf.h5" ]; then
        echo "  SKIP: po2_${ID}.scf.h5 already exists"
        continue
    fi

    JOB_OUTPUT=$(qsub -N po2_scf_${ID} -v GEOM_ID=$ID scf_single.pbs)
    JOB_ID=$(echo $JOB_OUTPUT | cut -d'.' -f1)
    echo "  Submitted SCF for po2_${ID}: $JOB_ID"

    if [ -z "$SCF_JOB_IDS" ]; then
        SCF_JOB_IDS="$JOB_ID"
    else
        SCF_JOB_IDS="${SCF_JOB_IDS}:$JOB_ID"
    fi
done

echo ""

if [ -n "$SCF_JOB_IDS" ]; then
    echo "Submitting autoCAS job with dependency on SCF jobs..."
    AUTOCAS_OUTPUT=$(qsub -W depend=afterok:${SCF_JOB_IDS} run_10geom.pbs)
    AUTOCAS_ID=$(echo $AUTOCAS_OUTPUT | cut -d'.' -f1)
    echo "  Submitted autoCAS: $AUTOCAS_ID"
    echo "  Depends on: $SCF_JOB_IDS"
else
    echo "All SCF files exist, submitting autoCAS directly..."
    AUTOCAS_OUTPUT=$(qsub run_10geom.pbs)
    AUTOCAS_ID=$(echo $AUTOCAS_OUTPUT | cut -d'.' -f1)
    echo "  Submitted autoCAS: $AUTOCAS_ID"
fi

echo ""
echo "=============================================="
echo "Monitor with: qstat -u \$USER"
echo "=============================================="
