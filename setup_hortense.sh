#!/bin/bash
# autoCAS4HE Environment Setup for VSC Hortense
# Usage: source setup_hortense.sh
#
# IMPORTANT: Edit INSTALL_DIR below to match your installation path

module --force purge
module load cluster/dodrio/cpu_milan_rhel9
module load GCCcore/12.3.0
module load GCC/12.3.0
module load Python/3.11.3-GCCcore-12.3.0
module load imkl/2023.1.0

# OpenMolcas + DMRG (for CASSCF/CASPT2 calculations)
module load QCMaquis/4.0.0-iomkl-2023a
module load OpenMolcas/25.06-iomkl-2023a-DMRG-no-MPI

# ==============================================================================
# EDIT THIS: Set to your installation directory
# ==============================================================================
INSTALL_DIR="/dodrio/scratch/projects/starting_2025_097/autoCAS4HE_built/autoCAS4HE"
# ==============================================================================

# Activate virtual environment
source ${INSTALL_DIR}/autocas_env/bin/activate

# Serenity paths (includes qcserenity shim)
export SERENITY_LIB_PATH="${INSTALL_DIR}/serenity/build/lib"
export SERENITY_RESOURCES="${INSTALL_DIR}/serenity/data/"
# Custom basis sets (ANO-RCC-VDZP, etc.) + standard Serenity basis sets
export SERENITY_BASIS_PATH="${INSTALL_DIR}/tests/custom_basis:${INSTALL_DIR}/serenity/data/basis/"
export LD_LIBRARY_PATH="${SERENITY_LIB_PATH}:$LD_LIBRARY_PATH"
export PYTHONPATH="${SERENITY_LIB_PATH}:$PYTHONPATH"
export PATH="${INSTALL_DIR}/serenity/build/bin:$PATH"

echo "========================================"
echo "autoCAS4HE environment loaded (Hortense)"
echo "========================================"
echo "  Serenity:    ${INSTALL_DIR}/serenity/build"
echo "  autoCAS:     $(which scine_autocas 2>/dev/null || echo 'not in PATH')"
echo "  Basis path:  ${SERENITY_BASIS_PATH}"
echo "========================================"
