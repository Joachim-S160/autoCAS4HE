#!/usr/bin/env python3
"""
Generate Po2 dissociation scaling test files.

Creates XYZ files, OpenMolcas SCF inputs, and PBS scripts for testing
autoCAS performance scaling with increasing numbers of geometries.

Distribution: Dense near equilibrium (~2.5 A), sparse toward dissociation (10 A).
  - 2.1 to 3.0 A: 0.1 A spacing  (10 points) -- near equilibrium
  - 3.0 to 5.0 A: 0.25 A spacing  (8 points) -- intermediate
  - 5.0 to 7.5 A: 0.5 A spacing   (5 points) -- sparse
  - 7.5 to 10.0 A: 1.25 A spacing (2 points) -- very sparse
  Total: 25 geometries
"""

import os

# ============================================================
# Dissociation distances (Angstrom)
# ============================================================
DISTANCES = [
    # Dense near equilibrium (~2.5 A)
    2.10, 2.20, 2.30, 2.40, 2.50, 2.60, 2.70, 2.80, 2.90, 3.00,
    # Medium density
    3.25, 3.50, 3.75, 4.00, 4.25, 4.50, 4.75, 5.00,
    # Sparse
    5.50, 6.00, 6.50, 7.00, 7.50,
    # Very sparse
    8.75, 10.00,
]

# Scaling test levels: how many geometries to use for each test
# Subsets are chosen to span the full dissociation range
SCALING_LEVELS = {
    2:  [4, 24],                                            # 2.50, 10.00
    5:  [0, 4, 9, 17, 24],                                 # 2.10, 2.50, 3.00, 5.00, 10.00
    10: [0, 2, 4, 6, 9, 12, 15, 17, 22, 24],               # spread across range
    15: [0, 1, 3, 4, 5, 7, 9, 11, 13, 15, 17, 19, 21, 23, 24],
    20: [0, 1, 2, 3, 4, 5, 6, 8, 9, 10, 12, 14, 16, 17, 19, 20, 21, 22, 23, 24],
    25: list(range(25)),                                     # all
}

# HPC settings
PBS_ACCOUNT = "2025_127"
PBS_EMAIL = "joachim.scheerlinck@ugent.be"
PROJECT = "starting_2025_097"
INSTALL_DIR = f"/dodrio/scratch/projects/{PROJECT}/autoCAS4HE_built/autoCAS4HE"


def write_xyz(directory, index, distance):
    """Write a Po2 XYZ file with atoms at +/- distance/2 on x-axis."""
    half = distance / 2.0
    filename = f"po2_{index:03d}.xyz"
    filepath = os.path.join(directory, filename)
    with open(filepath, "w") as f:
        f.write("2\n")
        f.write(f"Po2 molecule - {distance:.2f} Angstrom bond\n")
        f.write(f"Po  {-half:.6f}   0.000000   0.000000\n")
        f.write(f"Po   {half:.6f}   0.000000   0.000000\n")
    return filename


def write_scf_input(directory, index):
    """Write an OpenMolcas SCF input file with DKH2."""
    filename = f"po2_{index:03d}_scf.input"
    xyz_name = f"po2_{index:03d}.xyz"
    filepath = os.path.join(directory, filename)
    with open(filepath, "w") as f:
        f.write(f"&GATEWAY\n")
        f.write(f"  Coord = {xyz_name}\n")
        f.write(f"  Basis = ANO-RCC-VDZP\n")
        f.write(f"  Group = NoSym\n")
        f.write(f"\n")
        f.write(f"&SEWARD\n")
        f.write(f"  Cholesky\n")
        f.write(f"* Douglas-Kroll-Hess 2nd order relativistic Hamiltonian\n")
        f.write(f"  Relativistic = R02O\n")
        f.write(f"\n")
        f.write(f"&SCF\n")
        f.write(f"  Charge = 0\n")
        f.write(f"  Spin = 1\n")
    return filename


def write_generate_scf_pbs(directory):
    """Write PBS script to generate all .scf.h5 files via OpenMolcas DKH2."""
    filepath = os.path.join(directory, "generate_scf.pbs")
    n = len(DISTANCES)
    with open(filepath, "w") as f:
        f.write(f"""#!/bin/bash
# Generate OpenMolcas DKH2 SCF orbitals for all {n} Po2 geometries.
# Each geometry produces a .scf.h5 file needed by autoCAS.
#
# Submit with: qsub generate_scf.pbs

#PBS -N po2_scf_gen
#PBS -A {PBS_ACCOUNT}
#PBS -l nodes=1:ppn=16
#PBS -l walltime=06:00:00
#PBS -l mem=64gb
#PBS -M {PBS_EMAIL}
#PBS -m e

# ==============================================================================
# Setup
# ==============================================================================
PROJECT="{PROJECT}"
INSTALL_DIR="{INSTALL_DIR}"
source ${{INSTALL_DIR}}/setup_hortense.sh

cd $PBS_O_WORKDIR

echo "=============================================="
echo "  Po2 SCF Generation - {n} geometries"
echo "=============================================="
echo "Start: $(date)"
echo ""

FAILED=0
COMPLETED=0

""")
        for i in range(n):
            xyz = f"po2_{i:03d}.xyz"
            inp = f"po2_{i:03d}_scf.input"
            inp_stem = f"po2_{i:03d}_scf"
            h5 = f"po2_{i:03d}.scf.h5"
            workdir = f"po2_{i:03d}_workdir"
            f.write(f"""# --- Geometry {i}: {DISTANCES[i]:.2f} A ---
if [ ! -f "{h5}" ]; then
    echo "Running SCF for {xyz} ({DISTANCES[i]:.2f} A)..."
    mkdir -p {workdir}
    cd {workdir}
    cp ../{xyz} .
    cp ../{inp} .
    export MOLCAS_WORKDIR=$(pwd)/scratch
    mkdir -p $MOLCAS_WORKDIR
    pymolcas {inp} > {inp_stem}.log 2>&1
    SCF_EXIT=$?
    if [ $SCF_EXIT -eq 0 ] && [ -f "{inp_stem}/{inp_stem}.scf.h5" ]; then
        cp {inp_stem}/{inp_stem}.scf.h5 ../{h5}
        echo "  OK: {h5}"
        COMPLETED=$((COMPLETED + 1))
    else
        echo "  FAILED: {xyz} (exit=$SCF_EXIT)"
        FAILED=$((FAILED + 1))
    fi
    cd ..
else
    echo "  SKIP: {h5} already exists"
    COMPLETED=$((COMPLETED + 1))
fi

""")

        f.write(f"""echo ""
echo "=============================================="
echo "  SCF Generation Summary"
echo "=============================================="
echo "Completed: $COMPLETED / {n}"
echo "Failed:    $FAILED / {n}"
echo "End: $(date)"
""")


def write_scaling_pbs(directory, n_geom, indices):
    """Write a PBS script that runs autoCAS with n_geom geometries."""
    filepath = os.path.join(directory, f"run_scaling_{n_geom:02d}.pbs")

    # Build XYZ and orbital file lists
    xyz_files = [f"po2_{i:03d}.xyz" for i in indices]
    h5_files = [f"po2_{i:03d}.scf.h5" for i in indices]
    distances_used = [DISTANCES[i] for i in indices]

    # Estimate walltime: ~5 min per geometry + overhead
    walltime_hours = max(2, (n_geom * 10) // 60 + 1)
    # Estimate memory: scale with number of geometries
    mem_gb = min(128, 32 + n_geom * 4)

    with open(filepath, "w") as f:
        f.write(f"""#!/bin/bash
# Po2 autoCAS Scaling Test: {n_geom} geometries
# Distances: {', '.join(f'{d:.2f}' for d in distances_used)} A
#
# Measures wall time, CPU time, and peak memory for autoCAS
# with {n_geom} dissociation geometries.
#
# PREREQUISITE: Run generate_scf.pbs first to create .scf.h5 files.
# Submit with: qsub run_scaling_{n_geom:02d}.pbs

#PBS -N po2_scale_{n_geom:02d}
#PBS -A {PBS_ACCOUNT}
#PBS -l nodes=1:ppn=16
#PBS -l walltime={walltime_hours:02d}:00:00
#PBS -l mem={mem_gb}gb
#PBS -M {PBS_EMAIL}
#PBS -m e

# ==============================================================================
# Setup
# ==============================================================================
PROJECT="{PROJECT}"
INSTALL_DIR="{INSTALL_DIR}"
source ${{INSTALL_DIR}}/setup_hortense.sh

cd $PBS_O_WORKDIR
BASE_DIR=$(pwd)

echo "=============================================="
echo "  Po2 Scaling Test: {n_geom} geometries"
echo "=============================================="
echo "Start time: $(date)"
echo "Distances (A): {' '.join(f'{d:.2f}' for d in distances_used)}"
echo "PBS Job ID: $PBS_JOBID"
echo "Requested mem: {mem_gb}gb"
echo ""

# ==============================================================================
# Check that all .scf.h5 files exist
# ==============================================================================
MISSING=0
""")
        for h5 in h5_files:
            f.write(f"""if [ ! -f "{h5}" ]; then
    echo "ERROR: Missing {h5}"
    MISSING=$((MISSING + 1))
fi
""")

        f.write(f"""
if [ $MISSING -gt 0 ]; then
    echo "ERROR: $MISSING .scf.h5 files missing. Run generate_scf.pbs first."
    exit 1
fi
echo "All {n_geom} .scf.h5 files found."
echo ""

# ==============================================================================
# Create dedicated workdir for this scaling level
# ==============================================================================
WORKDIR="${{BASE_DIR}}/workdir_N{n_geom:02d}"
rm -rf "$WORKDIR"
mkdir -p "$WORKDIR"
cd "$WORKDIR"
export MOLCAS_WORKDIR="${{WORKDIR}}"

echo "Working directory: $WORKDIR"
echo ""

# ==============================================================================
# Build argument lists (use absolute paths since we cd into workdir)
# ==============================================================================
""")
        # XYZ args with absolute paths
        xyz_abs = [f"${{BASE_DIR}}/{x}" for x in xyz_files]
        f.write(f'XYZ_ARGS="{" ".join(xyz_abs)}"\n')

        # Orbital paths with absolute paths
        for i, h5 in enumerate(h5_files):
            if i == 0:
                f.write(f'ORB_PATHS="${{BASE_DIR}}/{h5}"\n')
            else:
                f.write(f'ORB_PATHS="${{ORB_PATHS}},${{BASE_DIR}}/{h5}"\n')

        f.write(f"""
# ==============================================================================
# Run autoCAS with timing and memory tracking
# ==============================================================================
echo "Running autoCAS with {n_geom} geometries..."
echo ""

# Record start time
START_SECONDS=$SECONDS

# Use /usr/bin/time for peak memory measurement (maxresident in KB)
/usr/bin/time -v scine_autocas_consistent_active_space \\
    -e \\
    -o "$ORB_PATHS" \\
    -b ANO-RCC-VDZP \\
    -m DMRGSCF \\
    $XYZ_ARGS \\
    2> ${{BASE_DIR}}/timing_{n_geom:02d}.txt

EXIT_CODE=$?
ELAPSED=$((SECONDS - START_SECONDS))

# ==============================================================================
# Results
# ==============================================================================
cd "$BASE_DIR"

echo ""
echo "=============================================="
echo "  Scaling Test Results: {n_geom} geometries"
echo "=============================================="
echo "Exit code:    $EXIT_CODE"
echo "Wall time:    ${{ELAPSED}}s ($((ELAPSED / 60))m $((ELAPSED % 60))s)"
echo "End time:     $(date)"
echo ""

# Extract peak memory from /usr/bin/time output
PEAK_MEM=0
if [ -f "timing_{n_geom:02d}.txt" ]; then
    PEAK_MEM=$(grep "Maximum resident" timing_{n_geom:02d}.txt | awk '{{print $NF}}')
    echo "Peak RSS:     ${{PEAK_MEM}} KB ($((PEAK_MEM / 1024)) MB)"
fi

# ==============================================================================
# Extract active space and copy output files
# ==============================================================================
if [ $EXIT_CODE -eq 0 ]; then
    FINAL_DIR="${{WORKDIR}}/autocas_project/final"
    RESULTS_DIR="${{BASE_DIR}}/results_N{n_geom:02d}"
    mkdir -p "$RESULTS_DIR"

    # Copy orbital files (.RasOrb) and HDF5 files for each geometry
    echo ""
    echo "--- Output files ---"
    if [ -d "$FINAL_DIR" ]; then
        cp "$FINAL_DIR"/system_*.RasOrb "$RESULTS_DIR/" 2>/dev/null
        cp "$FINAL_DIR"/system_*.rasscf.h5 "$RESULTS_DIR/" 2>/dev/null
        cp "$FINAL_DIR"/energies.dat "$RESULTS_DIR/" 2>/dev/null
        echo "  Copied RasOrb + rasscf.h5 + energies.dat to $RESULTS_DIR/"
        ls -la "$RESULTS_DIR/"
    else
        echo "  WARNING: $FINAL_DIR not found"
    fi

    # Extract active space info from the PBS stdout (this script's output)
    # We grep from the autoCAS stdout which is interleaved in this job's output
    echo ""
    echo "--- Active space summary ---"
    CAS_EO=$(grep -m1 "final CAS(e, o)" ${{WORKDIR}}/autocas_project/final/system_0.log 2>/dev/null || echo "not found")
    if [ "$CAS_EO" = "not found" ]; then
        # Fallback: check combined_cas_spaces file
        if [ -f "${{WORKDIR}}/autocas_project/final/combined_cas_spaces" ]; then
            echo "  Combined CAS spaces:"
            cat "${{WORKDIR}}/autocas_project/final/combined_cas_spaces"
            cp "${{WORKDIR}}/autocas_project/final/combined_cas_spaces" "$RESULTS_DIR/"
        fi
    fi

    # Extract energies
    if [ -f "$RESULTS_DIR/energies.dat" ]; then
        echo ""
        echo "--- Final energies ---"
        cat "$RESULTS_DIR/energies.dat"
    fi
fi

echo ""
echo "--- Full timing output ---"
if [ -f "timing_{n_geom:02d}.txt" ]; then
    cat timing_{n_geom:02d}.txt
fi

# Write summary to CSV-like file for easy parsing
echo "{n_geom},$EXIT_CODE,$ELAPSED,$PEAK_MEM" >> scaling_results.csv

echo ""
echo "Results appended to scaling_results.csv"
echo "Format: n_geom,exit_code,wall_time_s,peak_rss_kb"
""")


def write_submit_all(directory):
    """Write a script to submit all scaling tests."""
    filepath = os.path.join(directory, "submit_all.sh")
    with open(filepath, "w") as f:
        f.write(f"""#!/bin/bash
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
""")
        for n in sorted(SCALING_LEVELS.keys()):
            f.write(f"""JOBID=$(qsub $DEPEND run_scaling_{n:02d}.pbs)
echo "  N={n:2d} geometries: $JOBID"
""")

        f.write(f"""
echo ""
echo "All jobs submitted. Monitor with: qstat -u $USER"
echo "Results will be collected in scaling_results.csv"
""")
    os.chmod(filepath, 0o755)


def write_analyze_script(directory):
    """Write a script to analyze scaling results."""
    filepath = os.path.join(directory, "analyze_results.sh")
    with open(filepath, "w") as f:
        f.write("""#!/bin/bash
# Analyze Po2 scaling test results.
# Reads scaling_results.csv and prints a formatted table.
#
# Usage: ./analyze_results.sh

cd "$(dirname "$0")"

if [ ! -f "scaling_results.csv" ]; then
    echo "No scaling_results.csv found. Run the scaling tests first."
    exit 1
fi

echo "=============================================="
echo "  Po2 Scaling Test Results"
echo "=============================================="
echo ""
printf "%-10s %-10s %-15s %-15s\\n" "N_geom" "Status" "Wall_time" "Peak_RSS"
printf "%-10s %-10s %-15s %-15s\\n" "------" "------" "---------" "--------"

while IFS=',' read -r n_geom exit_code wall_time peak_rss; do
    if [ "$exit_code" = "0" ]; then
        status="OK"
    else
        status="FAIL($exit_code)"
    fi
    minutes=$((wall_time / 60))
    seconds=$((wall_time % 60))
    mem_mb=$((peak_rss / 1024))
    printf "%-10s %-10s %-15s %-15s\\n" "$n_geom" "$status" "${minutes}m ${seconds}s" "${mem_mb} MB"
done < scaling_results.csv

echo ""
echo "Raw data in scaling_results.csv"
echo "Detailed timing in timing_NN.txt files"
""")
    os.chmod(filepath, 0o755)


def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))

    print(f"Generating Po2 scaling test in: {base_dir}")
    print(f"Number of geometries: {len(DISTANCES)}")
    print()

    # Generate XYZ files
    print("Generating XYZ files...")
    for i, d in enumerate(DISTANCES):
        name = write_xyz(base_dir, i, d)
        print(f"  {name}: {d:.2f} A")

    # Generate OpenMolcas input files
    print("\nGenerating OpenMolcas SCF input files...")
    for i in range(len(DISTANCES)):
        name = write_scf_input(base_dir, i)
        print(f"  {name}")

    # Generate SCF PBS script
    print("\nGenerating generate_scf.pbs...")
    write_generate_scf_pbs(base_dir)

    # Generate scaling PBS scripts
    print("\nGenerating scaling PBS scripts...")
    for n, indices in sorted(SCALING_LEVELS.items()):
        write_scaling_pbs(base_dir, n, indices)
        dists = [f"{DISTANCES[i]:.2f}" for i in indices]
        print(f"  run_scaling_{n:02d}.pbs: {n} geometries ({', '.join(dists[:5])}{'...' if n > 5 else ''})")

    # Generate submission script
    print("\nGenerating submit_all.sh...")
    write_submit_all(base_dir)

    # Generate analysis script
    print("\nGenerating analyze_results.sh...")
    write_analyze_script(base_dir)

    # Print summary
    print("\n" + "=" * 60)
    print("  Summary")
    print("=" * 60)
    print(f"  Total geometries: {len(DISTANCES)}")
    print(f"  Range: {DISTANCES[0]:.2f} - {DISTANCES[-1]:.2f} A")
    print(f"  Scaling levels: {sorted(SCALING_LEVELS.keys())}")
    print()
    print("  Workflow:")
    print("  1. Pull changes on HPC:  git pull --recurse-submodules")
    print("  2. Rebuild Serenity")
    print("  3. Run:  ./submit_all.sh")
    print("     Or if .scf.h5 exist: ./submit_all.sh --no-scf")
    print("  4. After completion:  ./analyze_results.sh")


if __name__ == "__main__":
    main()
