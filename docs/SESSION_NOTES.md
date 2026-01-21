# Session Notes - 2026-01-21

## Summary of Work Completed

### 1. autoCAS4HE Repository Created
- GitHub repo: `Joachim-S160/autoCAS4HE` (private)
- Contains patched Serenity and autoCAS as submodules
- Both submodules on `heavy-elements-support` branch

### 2. Serenity Patches (completed locally, working)
Three files modified in `/home/joaschee/serenity/`:
- `src/basis/BasisFunctionProvider.cpp` - colon-separated `SERENITY_BASIS_PATH`
- `src/integrals/wrappers/Libint.h` - `N_PRIM_MAX` increased from 23 to 25
- `src/system/SystemController.cpp` - `SERENITY_BASIS_PATH` env var support

### 3. autoCAS Bug Fixed
- **File**: `scine_autocas/workflows/consistent_active_space/configuration.py:206`
- **Bug**: `"basis_set_set"` typo (should be `"basis_set"`)
- **Effect**: `-b` command line option was silently ignored, always using CC-PVDZ
- **Status**: Fixed and pushed to `Joachim-S160/autocas` fork

### 4. Verified Tests (local machine)
| Test | Basis | Result |
|------|-------|--------|
| N2 autoCAS | CC-PVDZ | CAS(6,6), -109.25/-108.94 a.u. |
| N2 autoCAS | ANO-RCC-VDZP | CAS(6,6), -109.04 a.u. |
| Po (one atom) HF (Serenity) | ANO-RCC-VDZP | Converged, -17349.15 a.u. |

## Current Issue: HPC Heap Corruption

### Problem
Running Po2 with ANO-RCC basis on HPC causes heap corruption:
```
corrupted size vs. prev_size (glibc heap corruption)
Location: run_scf() method during integral evaluation
```

### Root Cause (likely)
**HPC Serenity still uses original `N_PRIM_MAX=23`**, but ANO-RCC for Po requires 25 primitives per s-function.

### Solution Needed
Rebuild Serenity on HPC with patched `N_PRIM_MAX=25` in:
```
src/integrals/wrappers/Libint.h
```

Line to change:
```cpp
static const unsigned int N_PRIM_MAX = 25;  // was 23
```

## Next Steps

1. **Connect VSCode to HPC via SSH** (Remote-SSH extension)
2. **Rebuild Serenity on HPC** with N_PRIM_MAX fix
3. **Test Po2 autoCAS workflow** on HPC with ANO-RCC-VDZP
4. Consider using smaller test (Te2 instead of Po2) for faster iteration

## Key Paths (local machine)

| Item | Path |
|------|------|
| Serenity build | `/home/joaschee/serenity/build/` |
| autoCAS (editable) | `/home/joaschee/autocas/` |
| Python venv | `/home/joaschee/autocas_env/` |
| autoCAS4HE repo | `/home/joaschee/autoCAS4HE/` |
| ANO-RCC-VDZP basis | `/home/joaschee/serenity/data/basis/ANO-RCC-VDZP` |

## Environment Setup (local)
```bash
source /home/joaschee/autocas_env/bin/activate
export SERENITY_RESOURCES="/home/joaschee/serenity/data/"
export SERENITY_BASIS_PATH="/home/joaschee/serenity/data/basis/"
export LD_LIBRARY_PATH="/home/joaschee/serenity/build/lib:$LD_LIBRARY_PATH"
export PATH="/home/joaschee/serenity/bin:$PATH"
```

## Performance Note
Po2 SCF with ANO-RCC-VDZP takes ~30 min/iteration locally. Full autoCAS workflow (2 SCF + IBO + DMRG) would take 20+ hours. HPC recommended for production runs.
