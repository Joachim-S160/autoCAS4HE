# Building autoCAS4HE on VSC Tier-1 Hortense

This guide documents how to build the patched Serenity and autoCAS for heavy element calculations on the Hortense supercomputer (Dodrio cluster, cpu_milan_rhel9 partition).

## Overview

The autoCAS4HE project provides patched versions of:
- **Serenity**: `N_PRIM_MAX` increased from 23→25 for ANO-RCC basis sets
- **autoCAS**: Fix for `basis_set_set` typo that caused `-b` option to be ignored

## Prerequisites

- VSC account with access to Hortense
- Project allocation (e.g., `starting_2025_097`)
- GitHub access to `Joachim-S160/autoCAS4HE` repository

## Build Instructions

### Step 1: Clone the repository

```bash
cd /dodrio/scratch/projects/starting_2025_097/autoCAS4HE_built
git clone --recurse-submodules https://github.com/Joachim-S160/autoCAS4HE.git
cd autoCAS4HE
```

### Step 2: Load required modules

**Important:** We use GCC for compilation (Intel icpx 2023.1.0 has internal compiler bugs with Serenity). MKL is still used for BLAS/LAPACK performance.

```bash
module purge
module load cluster/dodrio/cpu_milan_rhel9
module load GCCcore/12.3.0
module load GCC/12.3.0
module load CMake/3.26.3-GCCcore-12.3.0
module load Ninja/1.11.1-GCCcore-12.3.0
module load Python/3.11.3-GCCcore-12.3.0
module load Eigen/3.4.0-GCCcore-12.3.0
module load Boost/1.82.0-GCC-12.3.0
module load libxc/6.2.2-GCC-12.3.0
module load imkl/2023.1.0
module load HDF5/1.14.0-gompi-2023a
```

### Step 3: Verify the N_PRIM_MAX patch

Before building, confirm the patch is applied:

```bash
cd serenity
grep "N_PRIM_MAX" src/integrals/wrappers/Libint.h
# Should show: static const unsigned int N_PRIM_MAX = 25;
```

### Step 4: Request an interactive job for building

Compilation is CPU-intensive. Request an interactive job with sufficient resources:

```bash
qsub -I -l walltime=04:00:00 -l nodes=1:ppn=16 -l mem=32gb -A 2025_127
```

Once in the job, reload the modules (same as Step 2):

```bash
module purge
module load cluster/dodrio/cpu_milan_rhel9
module load GCCcore/12.3.0
module load GCC/12.3.0
module load CMake/3.26.3-GCCcore-12.3.0
module load Ninja/1.11.1-GCCcore-12.3.0
module load Python/3.11.3-GCCcore-12.3.0
module load Eigen/3.4.0-GCCcore-12.3.0
module load Boost/1.82.0-GCC-12.3.0
module load libxc/6.2.2-GCC-12.3.0
module load imkl/2023.1.0
module load HDF5/1.14.0-gompi-2023a
```

### Step 5: Configure Serenity with CMake

```bash
cd /dodrio/scratch/projects/starting_2025_097/autoCAS4HE_built/autoCAS4HE/serenity
mkdir build && cd build

cmake .. \
  -G Ninja \
  -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_CXX_COMPILER=g++ \
  -DCMAKE_C_COMPILER=gcc \
  -DSERENITY_MARCH=native \
  -DSERENITY_USE_LIBXC=ON \
  -DSERENITY_DOWNLOAD_DEPENDENCIES=ON \
  -DSERENITY_PYTHON_BINDINGS=ON \
  -DPYTHON_EXECUTABLE=$(which python)
```

Note: `-G Ninja` generates Ninja build files. Without it, CMake generates Makefiles (use `make` instead of `ninja`).

Expected output:
```
-- Maximum angular momentum           : 5
-- Maximum angular momentum unrolling : 1
-- Configuring done
-- Generating done
```

### Step 6: Build Serenity

```bash
ninja -j 16
```

Build takes approximately 20-30 minutes with 16 cores. Expected final output:
```
[12510/12510] Linking CXX shared module lib/serenipy.so
```

### Step 7: Create qcserenity Python package shim

**Important:** The autoCAS code imports Serenity as `qcserenity.serenipy`, but the build only creates `serenipy.so`. We need to create a shim directory structure:

```bash
cd /dodrio/scratch/projects/starting_2025_097/autoCAS4HE_built/autoCAS4HE/serenity/build/lib
mkdir -p qcserenity
touch qcserenity/__init__.py
ln -s ../serenipy.so qcserenity/serenipy.so
```

Verify the shim works:
```bash
export PYTHONPATH="$(pwd):$PYTHONPATH"
python -c "import qcserenity.serenipy as spy; print('qcserenity shim OK')"
```

### Step 8: Fix autoCAS typo

Check and fix the basis_set typo:

```bash
cd /dodrio/scratch/projects/starting_2025_097/autoCAS4HE_built/autoCAS4HE
grep "basis_set_set" autocas/scine_autocas/workflows/consistent_active_space/configuration.py

# If typo exists, fix it:
sed -i 's/"basis_set_set"/"basis_set"/' autocas/scine_autocas/workflows/consistent_active_space/configuration.py

# Verify fix:
grep '"basis_set"' autocas/scine_autocas/workflows/consistent_active_space/configuration.py
```

### Step 9: Create Python virtual environment and install autoCAS

```bash
cd /dodrio/scratch/projects/starting_2025_097/autoCAS4HE_built/autoCAS4HE

python -m venv autocas_env
source autocas_env/bin/activate

pip install --upgrade pip
pip install -e autocas/
```

### Step 10: Verify installation

```bash
# Set PYTHONPATH for Serenity bindings (with qcserenity shim)
export PYTHONPATH="/dodrio/scratch/projects/starting_2025_097/autoCAS4HE_built/autoCAS4HE/serenity/build/lib:$PYTHONPATH"

# Test Python bindings
python -c "import serenipy; print('Serenity Python bindings: OK')"
python -c "import qcserenity.serenipy as spy; print('qcserenity shim: OK')"
python -c "import scine_autocas; print('autoCAS: OK')"
```

## Environment Setup Script

Create `setup_hortense.sh` in the installation directory:

```bash
#!/bin/bash
# autoCAS4HE Environment Setup for Hortense
# Usage: source setup_hortense.sh

module --force purge
module load cluster/dodrio/cpu_milan_rhel9
module load GCCcore/12.3.0
module load GCC/12.3.0
module load Python/3.11.3-GCCcore-12.3.0
module load imkl/2023.1.0

# OpenMolcas + DMRG (for CASSCF/CASPT2 calculations)
module load QCMaquis/4.0.0-iomkl-2023a
module load OpenMolcas/25.06-iomkl-2023a-DMRG-no-MPI

INSTALL_DIR="/dodrio/scratch/projects/starting_2025_097/autoCAS4HE_built/autoCAS4HE"

source ${INSTALL_DIR}/autocas_env/bin/activate

# Serenity paths (includes qcserenity shim)
export SERENITY_LIB_PATH="${INSTALL_DIR}/serenity/build/lib"
export SERENITY_RESOURCES="${INSTALL_DIR}/serenity/data/"
export SERENITY_BASIS_PATH="${INSTALL_DIR}/serenity/data/basis/"
export LD_LIBRARY_PATH="${SERENITY_LIB_PATH}:$LD_LIBRARY_PATH"
export PYTHONPATH="${SERENITY_LIB_PATH}:$PYTHONPATH"
export PATH="${INSTALL_DIR}/serenity/build/bin:$PATH"

echo "autoCAS4HE environment loaded"
echo "  Serenity: ${INSTALL_DIR}/serenity/build"
echo "  autoCAS:  $(which scine_autocas 2>/dev/null || echo 'not in PATH')"
```

## Testing the Installation

```bash
source setup_hortense.sh

# Test Python bindings
python -c "import serenipy; print('Serenity Python bindings: OK')"
python -c "import qcserenity.serenipy as spy; print('qcserenity shim: OK')"
python -c "import scine_autocas; print('autoCAS: OK')"

# Quick single-structure test
cd tests/autocas/N2_test
scine_autocas run -x n2_0.xyz -i molcas

# Consistent active space workflow (multiple structures)
scine_autocas_consistent_active_space -i 1 n2_0.xyz n2_1.xyz
```

## Using Custom Basis Sets

The patched Serenity supports `SERENITY_BASIS_PATH` with colon-separated directories:

```bash
export SERENITY_BASIS_PATH="/path/to/custom/basis:${INSTALL_DIR}/serenity/data/basis/"
```

Basis files must be in Turbomole format with filename matching the basis name (e.g., `ANO-RCC-VDZP`).

## Job Script Template

```bash
#!/bin/bash
#PBS -N autocas_job
#PBS -A 2025_127
#PBS -l nodes=1:ppn=16
#PBS -l walltime=24:00:00
#PBS -l mem=64gb

source /dodrio/scratch/projects/starting_2025_097/autoCAS4HE_built/autoCAS4HE/setup_hortense.sh

cd $PBS_O_WORKDIR

# Single structure autoCAS
scine_autocas run -x molecule.xyz -i molcas -b cc-pvdz

# Or consistent active space workflow with multiple structures
scine_autocas_consistent_active_space -i 1 structure1.xyz structure2.xyz -b ANO-RCC-VDZP
```

## Troubleshooting

### Intel compiler crash (icpx)
Intel icpx 2023.1.0 has internal compiler bugs with Serenity's template-heavy code. Use GCC instead:
```bash
-DCMAKE_CXX_COMPILER=g++ -DCMAKE_C_COMPILER=gcc
```

### Heap corruption with heavy elements
If you see `corrupted size vs. prev_size` errors, the `N_PRIM_MAX` patch is not applied. Rebuild Serenity from the patched source.

### `NameError: name 'spy' is not defined`
The qcserenity shim is missing. Create it:
```bash
cd ${INSTALL_DIR}/serenity/build/lib
mkdir -p qcserenity
touch qcserenity/__init__.py
ln -s ../serenipy.so qcserenity/serenipy.so
```

### Serenity Python bindings not found
Ensure `PYTHONPATH` includes the Serenity build lib directory:
```bash
export PYTHONPATH="${INSTALL_DIR}/serenity/build/lib:$PYTHONPATH"
```

### Basis set not found
1. Check `SERENITY_BASIS_PATH` is set correctly
2. Verify basis file exists and filename matches exactly (case-sensitive)
3. Use colon-separated paths if basis is in custom location

### `-b` option ignored (wrong basis used)
The `basis_set_set` typo causes this. Verify the fix:
```bash
grep '"basis_set"' autocas/scine_autocas/workflows/consistent_active_space/configuration.py
# Should NOT show "basis_set_set"
```

## Module Summary

| Module | Version | Purpose |
|--------|---------|---------|
| GCCcore | 12.3.0 | Base compiler toolchain |
| GCC | 12.3.0 | C/C++ compilers (used instead of Intel due to icpx bugs) |
| imkl | 2023.1.0 | Intel MKL for BLAS/LAPACK performance |
| CMake | 3.26.3 | Build system |
| Ninja | 1.11.1 | Fast parallel builds |
| Python | 3.11.3 | Python runtime |
| Boost | 1.82.0 | C++ libraries |
| HDF5 | 1.14.0 | Data format library |
| libxc | 6.2.2 | DFT functionals |
| Eigen | 3.4.0 | Linear algebra templates |
| OpenMolcas | 25.06 | CASSCF/CASPT2 |
| QCMaquis | 4.0.0 | DMRG solver |

## References

- [autoCAS documentation](https://scine.ethz.ch/download/autocas)
- [Serenity documentation](https://github.com/qcserenity/serenity)
- [VSC Hortense documentation](https://docs.vscentrum.be/en/latest/gent/tier1_hortense.html)

---
*Last updated: 2026-01-22*
*Build tested on: Dodrio cpu_milan_rhel9 partition with GCC 12.3.0*
*N2 consistent active space test: CAS(6,6) successfully identified*
