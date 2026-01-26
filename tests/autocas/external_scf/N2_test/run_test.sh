#!/bin/bash
# Test script for autoCAS with external OpenMolcas orbitals
# This tests the new -e flag functionality

set -e  # Exit on error

source ~/autoCAS4HE/setup_autocas_env.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=============================================="
echo "  N2 autoCAS Test with External Orbitals"
echo "=============================================="

# Step 1: Generate OpenMolcas SCF orbitals
echo ""
echo "Step 1: Running OpenMolcas SCF for both geometries..."
echo ""

# Create work directories
mkdir -p n2_0_workdir n2_1_workdir

# Run OpenMolcas for geometry 0
echo "Running OpenMolcas SCF for n2_0 (1.1 Å)..."
cd n2_0_workdir
cp ../n2_0.xyz .
cp ../n2_0_scf.input .
pymolcas n2_0_scf.input > n2_0_scf.log 2>&1
if [ -f "$MOLCAS_WORKDIR/n2_0_scf.ScfOrb" ]; then
    cp "$MOLCAS_WORKDIR/n2_0_scf.ScfOrb" ../n2_0.ScfOrb
elif [ -f "n2_0_scf.ScfOrb" ]; then
    cp n2_0_scf.ScfOrb ../n2_0.ScfOrb
else
    echo "ERROR: Could not find n2_0 ScfOrb file"
    exit 1
fi
cd ..

# Run OpenMolcas for geometry 1
echo "Running OpenMolcas SCF for n2_1 (4.1 Å)..."
cd n2_1_workdir
cp ../n2_1.xyz .
cp ../n2_1_scf.input .
pymolcas n2_1_scf.input > n2_1_scf.log 2>&1
if [ -f "$MOLCAS_WORKDIR/n2_1_scf.ScfOrb" ]; then
    cp "$MOLCAS_WORKDIR/n2_1_scf.ScfOrb" ../n2_1.ScfOrb
elif [ -f "n2_1_scf.ScfOrb" ]; then
    cp n2_1_scf.ScfOrb ../n2_1.ScfOrb
else
    echo "ERROR: Could not find n2_1 ScfOrb file"
    exit 1
fi
cd ..

echo "OpenMolcas SCF completed. Orbital files generated:"
ls -la *.ScfOrb

# Step 2: Run autoCAS with external orbitals
echo ""
echo "Step 2: Running autoCAS with external orbitals (-e flag)..."
echo ""

# Get absolute paths
N2_0_ORB="$(pwd)/n2_0.ScfOrb"
N2_1_ORB="$(pwd)/n2_1.ScfOrb"

# Run autoCAS consistent active space protocol with external orbitals
scine_autocas_consistent_active_space -e -o "$N2_0_ORB,$N2_1_ORB" -b ANO-RCC-VDZP n2_0.xyz n2_1.xyz

echo ""
echo "=============================================="
echo "  Test completed!"
echo "=============================================="
echo ""
echo "Check the output files for results."
