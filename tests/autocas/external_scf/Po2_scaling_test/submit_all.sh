#!/bin/bash
# Submit all Po2 scaling tests.
#
# Usage:
#   ./submit_all.sh          # Submit SCF generation + all scaling tests
#   ./submit_all.sh --no-scf # Skip SCF generation (if .scf.h5 files already exist)

cd "$(dirname "$0")"

if [ "$1" != "--no-scf" ]; then
    echo "Submitting SCF generation job..."
    SCF_JOBID=$(qsub generate_scf.pbs)
    echo "  SCF Job: $SCF_JOBID"
    echo ""
    echo "Submitting scaling tests (will wait for SCF to finish)..."
    DEPEND="-W depend=afterok:$SCF_JOBID"
else
    echo "Skipping SCF generation (--no-scf flag)."
    echo "Submitting scaling tests..."
    DEPEND=""
fi

echo ""
JOBID=$(qsub $DEPEND run_scaling_02.pbs)
echo "  N= 2 geometries: $JOBID"
JOBID=$(qsub $DEPEND run_scaling_05.pbs)
echo "  N= 5 geometries: $JOBID"
JOBID=$(qsub $DEPEND run_scaling_10.pbs)
echo "  N=10 geometries: $JOBID"
JOBID=$(qsub $DEPEND run_scaling_15.pbs)
echo "  N=15 geometries: $JOBID"
JOBID=$(qsub $DEPEND run_scaling_20.pbs)
echo "  N=20 geometries: $JOBID"
JOBID=$(qsub $DEPEND run_scaling_25.pbs)
echo "  N=25 geometries: $JOBID"

echo ""
echo "All jobs submitted. Monitor with: qstat -u $USER"
echo "Results will be collected in scaling_results.csv"
