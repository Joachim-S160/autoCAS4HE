# IBO Rydberg Orbital Overflow Fix for Heavy Elements

## Status: EXPERIMENTAL - NOT RECOMMENDED

**This fix was moved to branch `rydberg-cap-experimental` and reverted from `heavy-elements-support`.**

The fix prevents one crash but causes another problem: **zero valence virtual orbitals**, which breaks IBO localization in a different way.

## Summary

This document describes an attempted fix in Serenity's `LocalizationTask.cpp` for the "core orbital assigned to be virtual" crash when running IBO localization on heavy element systems like Po₂. **The fix is not viable** because it causes all virtual orbitals to be classified as Rydberg, leaving no valence virtuals for IBO to work with.

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

## Problem with This Fix: Zero Valence Virtuals

### The Issue

While the cap prevents the "core orbital assigned to be virtual" crash, it creates a new problem:

| Orbital Type | Count | Result |
|--------------|-------|--------|
| Core occupied | 62 | ε < -5.0 Ha |
| Valence occupied | 22 | ε > -5.0 Ha |
| **Valence virtual** | **0** | All marked as Rydberg! |
| Rydberg | 52 | All virtuals |

IBO localization **requires valence virtual orbitals** to form proper intrinsic bond orbitals. With zero valence virtuals, the localization fails with a different error:

```
RuntimeError: The IBO localization basis is too small to localize the given orbital selection.
```

### Why This Happens

The fix caps `nRydberg` at `nVirtuals = 52`, meaning **all 52 virtual orbitals are classified as Rydberg**. This leaves:
- `nValenceVirtuals = nVirtuals - nRydberg = 52 - 52 = 0`

IBO needs valence virtuals to project onto the minimal basis (MINAO) for localization. With none available, it cannot proceed.

---

## Conclusion: IBO is Fundamentally Incompatible with Po₂

The root cause is that **MINAO for Po is too small** (13 functions per atom) relative to:
- The full basis (68 functions per atom in ANO-RCC-VDZP)
- The number of occupied orbitals (42 per atom)

This creates an impossible situation:
1. **Without the cap**: `nRydberg = 110 > nVirtuals = 52` → overflow into occupied → crash
2. **With the cap**: `nRydberg = 52 = nVirtuals` → zero valence virtuals → IBO fails

**IBO localization cannot work for Po₂ with the current MINAO definition.**

---

## Recommended Alternatives

1. **Use different localization method**: Pipek-Mezey (PM) or Foster-Boys (FB) don't rely on MINAO
2. **Expand MINAO for Po**: Add more shells to the Po MINAO definition
3. **Use energy-based Rydberg detection**: Instead of `nBasis - nMINAO`, use energy cutoff

See [next_steps.md](../../docs/next_steps.md) for the development roadmap.

---

## Why This Fix is Correct (Historical Note)

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

## Commit History

```
Commit: c61b7dc (serenity/rydberg-cap-experimental)
Message: Fix IBO Rydberg overflow for heavy elements
Status: EXPERIMENTAL - moved to separate branch

Commit: 8b816a0 (serenity/heavy-elements-support)
Message: Revert "Fix IBO Rydberg overflow for heavy elements"
Status: Reverted due to zero valence virtuals issue
```

## Error Messages Reference

### Error 1: Without the cap (current state)
```
RuntimeError: The IBO localization basis is too small to localize the given orbital selection.
```

### Error 2: With the cap (experimental branch)
```
RuntimeError: A core orbital is assigned to be virtual. Something is wrong here!
```

Both errors indicate **IBO is incompatible with Po₂** using the current MINAO definition.
