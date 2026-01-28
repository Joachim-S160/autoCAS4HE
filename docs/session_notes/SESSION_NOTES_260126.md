# Session Notes: 2026-01-26

## Summary

Identified and fixed the root cause of the "core orbital assigned to be virtual" crash in IBO localization for heavy elements (Po₂).

---

## Problem Statement

When running autoCAS with external DKH2 orbitals for Po₂, Serenity's IBO localization crashed with:
```
RuntimeError: A core orbital is assigned to be virtual. Something is wrong here!
```

This occurred even after correctly loading relativistic (DKH2) orbitals from OpenMolcas.

---

## Investigation Path

### Initial Hypothesis: Wrong Eigenvalues
- Thought Serenity wasn't reading DKH2 eigenvalues from `.scf.h5` files
- Fixed protocol.py to copy `.scf.h5` (HDF5) instead of `.ScfOrb` (ASCII)
- Verified DKH2 eigenvalues were correct in HDF5 file (1s at -3431 Ha)
- **Result**: Still crashed with same error

### Root Cause Discovery
Examined Serenity source code (`LocalizationTask.cpp`) and found:

```cpp
const unsigned int nRydbergOrbitals = std::max(0, int(nBasisFunctions) - nMinimalBasisFunctions);
```

For Po₂:
| Property | Value |
|----------|-------|
| nBasisFunctions (ANO-RCC-VDZP) | 136 |
| nMinimalBasisFunctions (MINAO) | 26 |
| nOccupied | 84 |
| nVirtuals | 52 |
| **Calculated nRydberg** | **110** |

The algorithm tried to mark 110 orbitals as Rydberg, but only 52 virtuals exist. It overflowed into occupied orbitals, some of which were flagged as core.

---

## Solution

Modified `serenity/src/tasks/LocalizationTask.cpp` to cap `nRydbergOrbitals` at the number of virtual orbitals:

```cpp
unsigned int nRydbergOrbitals = std::max(0, int(nBasisFunctions) - nMinimalBasisFunctions);

// Find minimum number of virtuals across all spins
unsigned int minVirtuals = nBasisFunctions;
for_spin(nOcc) {
  const unsigned int nVirtuals = nBasisFunctions - nOcc_spin;
  if (nVirtuals < minVirtuals) minVirtuals = nVirtuals;
};

if (nRydbergOrbitals > minVirtuals) {
  OutputControl::mOut << "  Note: Capping Rydberg orbitals from " << nRydbergOrbitals
                      << " to " << minVirtuals << " (number of virtuals)." << std::endl;
  nRydbergOrbitals = minVirtuals;
}
```

---

## Files Changed

### Serenity (heavy-elements-support branch)
- `src/tasks/LocalizationTask.cpp` - Added Rydberg cap logic

### autoCAS (heavy-elements-support branch)
- `scine_autocas/workflows/consistent_active_space/protocol.py` - Fixed to copy `.scf.h5` files, removed debug code

### Parent Repo (main branch)
- `research/localization/IBO_RYDBERG_OVERFLOW_FIX.md` - Documentation of the fix

---

## Commits

1. **Serenity** `c61b7dc`: Fix IBO Rydberg overflow for heavy elements
2. **autoCAS** `df1af70`: Remove debug code from protocol.py
3. **Parent** `ff6d249`: Add research doc explaining IBO Rydberg overflow fix

---

## Next Steps

1. Rebuild Serenity on HPC (requires interactive job with build modules)
2. Test Po₂ external orbital workflow
3. If successful, run full autoCAS workflow with DMRG

---

## Key Learnings

1. **MINAO basis is small for heavy elements**: Po has only 13 MINAO functions (2s + 6p + 5d) vs 68 ANO-RCC-VDZP functions per atom

2. **IBO assumptions don't hold for heavy elements**: The formula `nRydberg = nBasis - nMinao` assumes light elements where this is always ≤ nVirtuals

3. **File formats matter**: Serenity reads eigenvalues from `.scf.h5` (HDF5), not `.ScfOrb` (ASCII)

4. **Source code access is valuable**: This bug could only be found by reading Serenity's C++ source, not by debugging at the Python level

---

## HPC Build Commands

```bash
# Request interactive job
qsub -I -l walltime=04:00:00 -l nodes=1:ppn=16 -l mem=32gb -A $PROJECT

# Load modules and build
module load ... # see HPC_BUILD_HORTENSE.md
cd serenity/build
ninja -j 16
```

---

## Related Documents

- [research/localization/IBO_RYDBERG_OVERFLOW_FIX.md](../research/localization/IBO_RYDBERG_OVERFLOW_FIX.md)
- [docs/HPC_BUILD_HORTENSE.md](HPC_BUILD_HORTENSE.md)
- [NOTETOSELF](../NOTETOSELF) - Previous debugging notes
