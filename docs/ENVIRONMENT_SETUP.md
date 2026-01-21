# Environment Setup for autoCAS4HE

This guide documents the exact environment setup required to run autoCAS with the patched Serenity build for heavy elements and custom basis sets.

## Prerequisites

- Python 3.11 virtual environment (`autocas_env`)
- OpenMolcas with QCMaquis (DMRG) support
- Patched Serenity build (from this repository's submodule)

## Directory Structure

```
/home/joaschee/
├── autocas_env/              # Python virtual environment
├── serenity/                 # Patched Serenity build (working copy)
│   ├── build/
│   │   ├── bin/              # serenity binary
│   │   └── lib/              # serenipy.so (Python bindings)
│   └── data/                 # basis sets, initial guesses, etc.
├── autocas/                  # autoCAS source (editable install)
├── OpenMolcas/
│   └── build/
│       └── pymolcas          # OpenMolcas Python driver
└── autoCAS4HE/               # This repository
```

## Environment Variables

The following environment variables must be set before running autoCAS:

```bash
# Activate the Python environment
source /home/joaschee/autocas_env/bin/activate

# Serenity resources (basis sets, initial guesses, etc.)
export SERENITY_RESOURCES="/home/joaschee/serenity/data/"

# Custom basis set search path (colon-separated)
# First path is for custom basis sets, second is the default Serenity basis
export SERENITY_BASIS_PATH="/path/to/custom/basis:/home/joaschee/serenity/data/basis/"

# Library path for Serenity shared libraries (required for serenipy)
export LD_LIBRARY_PATH="/home/joaschee/serenity/build/lib:$LD_LIBRARY_PATH"

# Add Serenity binary to PATH
export PATH="/home/joaschee/serenity/bin:$PATH"
```

## Quick Setup Script

Create a file `setup_autocas_env.sh`:

```bash
#!/bin/bash
# Setup environment for autoCAS with patched Serenity

source /home/joaschee/autocas_env/bin/activate
export SERENITY_RESOURCES="/home/joaschee/serenity/data/"
export SERENITY_BASIS_PATH="/home/joaschee/serenity/data/basis/"
export LD_LIBRARY_PATH="/home/joaschee/serenity/build/lib:$LD_LIBRARY_PATH"
export PATH="/home/joaschee/serenity/bin:$PATH"

echo "autoCAS environment activated"
echo "  SERENITY_RESOURCES: $SERENITY_RESOURCES"
echo "  LD_LIBRARY_PATH includes: /home/joaschee/serenity/build/lib"
```

Usage:
```bash
source setup_autocas_env.sh
```

## Verified Test: N2 Consistent Active Space

The following test was successfully run on 2026-01-21:

```bash
# Set up environment
source /home/joaschee/autocas_env/bin/activate
export SERENITY_RESOURCES="/home/joaschee/serenity/data/"
export LD_LIBRARY_PATH="/home/joaschee/serenity/build/lib:$LD_LIBRARY_PATH"
export PATH="/home/joaschee/serenity/bin:$PATH"

# Create test directory
mkdir -p /home/joaschee/autoCAS4HE/tests/N2_test
cd /home/joaschee/autoCAS4HE/tests/N2_test

# Create test files
cat > n2_0.xyz << 'EOF'
2

N 0 0 0
N 0 0 1.1
EOF

cat > n2_1.xyz << 'EOF'
2

N 0 0 0
N 0 0 4.1
EOF

# Run autoCAS consistent active space protocol
scine_autocas_consistent_active_space -i 1 n2_0.xyz n2_1.xyz
```

### Expected Output

- Serenity HF calculations for both geometries
- IBO localization and orbital alignment
- Direct orbital selection (DOS) partitioning
- DMRG calculation via OpenMolcas/QCMaquis
- Active space selection: **CAS(6,6)** (6 electrons, 6 orbitals)
- Final CASPT2 energies:
  - N2 at 1.1 Å: ~-109.25 a.u.
  - N2 at 4.1 Å: ~-108.94 a.u.

## qcserenity Python Bindings

The `qcserenity` package was set up manually to use the local Serenity build:

Location: `/home/joaschee/autocas_env/lib/python3.11/site-packages/qcserenity/`

This package:
1. Sets `SERENITY_RESOURCES` if not already set
2. Adds the Serenity build lib to `sys.path`
3. Provides `qcserenity.serenipy` via symlink to `/home/joaschee/serenity/build/lib/serenipy.so`

**Important**: `LD_LIBRARY_PATH` must be set *before* Python starts to avoid library conflicts.

## Serenity Patches

The patched Serenity includes these changes (see `serenity-heavy-elements.patch`):

1. **`src/basis/BasisFunctionProvider.cpp`**: Support for `SERENITY_BASIS_PATH` with colon-separated directories
2. **`src/integrals/wrappers/Libint.h`**: Increased `N_PRIM_MAX` from 23 to 25 for ANO-RCC basis sets
3. **`src/system/SystemController.cpp`**: Added `SERENITY_BASIS_PATH` environment variable support

## Troubleshooting

### "NameError: name 'spy' is not defined"
- Cause: `qcserenity.serenipy` import failed silently
- Solution: Ensure `LD_LIBRARY_PATH` is set before running Python

### "ImportError: generic_type: type 'BASIC_FUNCTIONALS' is already registered"
- Cause: Library conflict when serenipy is loaded
- Solution: Set `LD_LIBRARY_PATH` before Python starts, not via Python code

### "ERROR: Environment variable SERENITY_RESOURCES not set"
- Cause: Serenity needs this for various data files beyond basis sets
- Solution: `export SERENITY_RESOURCES="/home/joaschee/serenity/data/"`
