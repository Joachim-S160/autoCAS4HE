# IBO Rydberg Orbital Overflow Fix for Heavy Elements

## Summary

This document describes a bug fix in Serenity's `LocalizationTask.cpp` that resolves the "core orbital assigned to be virtual" crash when running IBO localization on heavy element systems like Po₂.

---

## Background: What are Rydberg Orbitals?

**Rydberg orbitals** are diffuse, high-energy virtual orbitals that extend far from the molecular core. In quantum chemistry:

- They represent excited states where electrons are promoted to very high principal quantum numbers
- They have large spatial extent and weak binding to the nucleus
- In basis set calculations, they correspond to the most diffuse basis functions

In the context of orbital localization:
- **Valence virtual orbitals**: Compact, chemically relevant virtual orbitals (antibonding σ*, π*, etc.)
- **Rydberg orbitals**: Diffuse, less chemically relevant orbitals that can interfere with localization

---

## How Serenity Uses Rydberg Classification in IBO

The Intrinsic Bond Orbital (IBO) localization method in Serenity separates orbitals into categories:

1. **Core orbitals**: Deep, atomic-like orbitals (e.g., 1s, 2s, 2p for heavy atoms)
2. **Valence occupied orbitals**: Chemically active bonding orbitals
3. **Valence virtual orbitals**: Low-lying antibonding orbitals
4. **Rydberg orbitals**: High-energy diffuse virtual orbitals

### The Algorithm

```
For IBO localization:
1. Determine core orbitals by energy cutoff (ε < -5.0 Ha → core)
2. Calculate Rydberg count: nRydberg = nBasisFunctions - nMinimalBasisFunctions
3. Mark the nRydberg orbitals with HIGHEST eigenvalues as Rydberg
4. Localize valence occupied and valence virtual separately
5. Keep core and Rydberg orbitals canonical (not localized)
```

The **minimal basis** (MINAO) represents the minimum number of functions needed to describe atomic orbitals. The assumption is that `nBasisFunctions - nMinimalBasis` gives the number of "extra" diffuse functions that form Rydberg orbitals.

---

## The Bug: Rydberg Overflow for Heavy Elements

### Problem

For heavy elements like Polonium (Z=84), the minimal basis (MINAO) is relatively small compared to the full basis set:

| Property | Po₂ Value |
|----------|-----------|
| ANO-RCC-VDZP basis functions | 136 |
| MINAO basis functions | 26 (13 per Po) |
| Occupied orbitals | 84 |
| Virtual orbitals | 52 |
| **Calculated nRydberg** | **110** |

The algorithm calculated `nRydberg = 136 - 26 = 110`, but there are only **52 virtual orbitals**!

### Consequence

When marking 110 orbitals as Rydberg by selecting the 110 highest eigenvalues:
- All 52 virtuals were selected (correct)
- Plus 58 occupied orbitals with the highest energies (incorrect!)
- Some of these occupied orbitals were already flagged as "core" (ε < -5.0 Ha)
- → **Crash**: "A core orbital is assigned to be virtual"

### Root Cause

The original code in `LocalizationTask.cpp`:
```cpp
const unsigned int nRydbergOrbitals = std::max(0, int(nBasisFunctions) - nMinimalBasisFunctions);
this->_systemController->...->setRydbergOrbitalsByNumber(nRydbergOrbitals);
```

This assumes `nRydberg ≤ nVirtuals`, which holds for light elements but fails for heavy elements where the minimal basis is small relative to the full basis.

---

## The Fix

### Code Change

Location: `serenity/src/tasks/LocalizationTask.cpp`, lines 152-173

```cpp
// Calculate nRydbergOrbitals but cap at number of virtual orbitals to prevent overflow
// into occupied space (important for heavy elements with small minimal basis)
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

this->_systemController->...->setRydbergOrbitalsByNumber(nRydbergOrbitals);
```

### Effect

For Po₂:
- Before: `nRydberg = 110` → crash (overflows into occupied)
- After: `nRydberg = min(110, 52) = 52` → all virtuals marked as Rydberg, no overflow

---

## Why This Fix is Correct

1. **Physical interpretation**: Rydberg orbitals are virtual orbitals. It makes no physical sense to classify occupied orbitals as Rydberg.

2. **Conservative approach**: By capping at `nVirtuals`, we ensure all virtuals can potentially be Rydberg, but we never touch occupied orbitals.

3. **Backward compatible**: For light elements where `nRydberg < nVirtuals`, the behavior is unchanged.

4. **Handles UNRESTRICTED**: The fix finds the minimum `nVirtuals` across alpha/beta spins, ensuring correctness for open-shell systems.

---

## Affected Systems

This bug affects any system where:
```
nBasisFunctions - nMinimalBasisFunctions > nBasisFunctions - nOccupied
```

Simplifying:
```
nOccupied > nMinimalBasisFunctions
```

This is common for:
- Heavy elements (Z > 50) with small MINAO definitions
- Large basis sets (ANO-RCC, aug-cc-pVTZ, etc.)
- Systems with many electrons

---

## References

- Serenity source: `src/tasks/LocalizationTask.cpp`
- IBO method: Knizia, G. J. Chem. Theory Comput. 2013, 9, 4834-4843
- MINAO basis: Minimal atomic natural orbital basis for IAO projection

---

## Commit

```
Commit: c61b7dc (serenity/heavy-elements-support)
Message: Fix IBO Rydberg overflow for heavy elements
```
