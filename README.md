# autoCAS4HE - autoCAS for Heavy Elements

This repository provides patched versions of [Serenity](https://github.com/qcserenity/serenity) and [autoCAS](https://github.com/qcscine/autocas) that enable using custom basis sets in Turbomole format (such as ANO-RCC-VQZP) for heavy element calculations.

## Problem

The standard Serenity installation has issues that prevent using custom basis sets like ANO-RCC-VQZP for heavy elements:

1. **Limited basis set search paths**: Serenity only looks for basis sets in a single directory
2. **Primitive limit too low**: The `N_PRIM_MAX` constant was set to 23, but ANO-RCC basis sets require up to 25 primitives per basis function
3. **Silent fallback**: When a basis set isn't found, Serenity silently falls back to CC-PVDZ instead of raising an error

Related issues:
- [qcserenity/serenity#18](https://github.com/qcserenity/serenity/issues/18)
- [qcscine/autocas#18](https://github.com/qcscine/autocas/issues/18)

## Repository Structure

```
autoCAS4HE/
├── serenity/                 # Patched Serenity (submodule)
├── autocas/                  # Patched autoCAS (submodule)
├── tests/
│   ├── custom_basis/         # Custom basis sets (ANO-RCC-VDZP, etc.)
│   ├── serenity/             # Serenity-only tests
│   │   └── Po2_HF/           # Polonium HF test
│   └── autocas/              # autoCAS workflow tests
│       ├── N2_test/          # N2 with CC-PVDZ
│       └── N2_ANO_test/      # N2 with ANO-RCC-VDZP
├── docs/
│   ├── ENVIRONMENT_SETUP.md  # Detailed environment setup guide
│   └── HPC_BUILD_HORTENSE.md # HPC build guide for VSC Hortense
├── setup_autocas_env.sh      # Quick environment setup script
└── serenity-heavy-elements.patch
```

## Quick Start

### 1. Clone with submodules

```bash
git clone --recurse-submodules https://github.com/Joachim-S160/autoCAS4HE.git
cd autoCAS4HE
```

### 2. Build Serenity

```bash
cd serenity
mkdir build && cd build
cmake -G Ninja .. \
  -DSERENITY_PYTHON=ON \
  -DSERENITY_PYTHON_BINDINGS=ON \
  -DBUILD_TESTING=OFF \
  -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_INTERPROCEDURAL_OPTIMIZATION=OFF \
  -DCMAKE_CXX_FLAGS="-O2 -g0 -fno-lto -pipe"
ninja -j1
cd ../..
```

### 3. Set up environment

```bash
source setup_autocas_env.sh
```

Or manually:
```bash
source /path/to/autocas_env/bin/activate
export SERENITY_RESOURCES="/path/to/serenity/data/"
export SERENITY_BASIS_PATH="/path/to/custom/basis:/path/to/serenity/data/basis/"
export LD_LIBRARY_PATH="/path/to/serenity/build/lib:$LD_LIBRARY_PATH"
export PATH="/path/to/serenity/bin:$PATH"
```

### 4. Run test

```bash
cd tests/autocas/N2_test
scine_autocas_consistent_active_space -i 1 n2_0.xyz n2_1.xyz
```

Or with a custom basis set:
```bash
scine_autocas_consistent_active_space -i 1 -b ANO-RCC-VDZP n2_0.xyz n2_1.xyz
```

## Serenity Patches

### 1. `src/basis/BasisFunctionProvider.cpp`
- Added support for colon-separated search paths via `SERENITY_BASIS_PATH`
- Improved error messages showing which directories were searched

### 2. `src/integrals/wrappers/Libint.h`
- Increased `N_PRIM_MAX` from 23 to 25 to support ANO-RCC basis sets

### 3. `src/system/SystemController.cpp`
- Added `SERENITY_BASIS_PATH` environment variable support
- Falls back to `SERENITY_RESOURCES/basis/` for backwards compatibility

## autoCAS Patches

### 1. `scine_autocas/workflows/consistent_active_space/configuration.py`
- Fixed typo: `basis_set_set` → `basis_set` in `get_serenity_interface_settings()`
- This bug caused the `-b` command line option to be silently ignored, falling back to CC-PVDZ

## Verified Tests

### Local Machine (WSL2)

| Test | Basis | Active Space | Energies (a.u.) |
|------|-------|--------------|-----------------|
| N2 autoCAS | CC-PVDZ | CAS(6,6) | -109.25 / -108.94 |
| N2 autoCAS | ANO-RCC-VDZP | CAS(6,6) | -109.36 / -109.04 |
| Po HF (Serenity) | ANO-RCC-VDZP | - | -17349.15 |

### HPC (VSC Tier-1 Hortense)

| Test | Basis | Active Space | Energies (a.u.) |
|------|-------|--------------|-----------------|
| N2 autoCAS | CC-PVDZ | CAS(6,6) | -109.25 / -108.94 |
| N2 autoCAS | ANO-RCC-VDZP | CAS(6,6) | -109.36 / -109.04 |

**Notes:**
- N2 geometries: 1.1 Å (equilibrium) and 4.1 Å (dissociated)
- ANO-RCC-VDZP requires the `N_PRIM_MAX=25` patch and `-b` option fix
- HPC build uses GCC 12.3.0 (Intel icpx has compiler bugs with Serenity)

## Custom Basis Sets

Custom basis sets are stored in `tests/custom_basis/` and included via `SERENITY_BASIS_PATH`.

**Included:**
- `ANO-RCC-VDZP` - All-electron relativistic basis for heavy elements

**Adding new basis sets:**
1. Place file in `tests/custom_basis/`
2. Filename must match basis name exactly (e.g., `ANO-RCC-VTZP`)
3. Format: Turbomole format

## Documentation

- [docs/ENVIRONMENT_SETUP.md](docs/ENVIRONMENT_SETUP.md) - Local setup instructions
- [docs/HPC_BUILD_HORTENSE.md](docs/HPC_BUILD_HORTENSE.md) - HPC build guide for VSC Tier-1 Hortense

## License

- Serenity: LGPL-3.0 ([license](https://github.com/qcserenity/serenity/blob/master/LICENSE))
- autoCAS: BSD-3-Clause ([license](https://github.com/qcscine/autocas/blob/master/LICENSE.txt))
