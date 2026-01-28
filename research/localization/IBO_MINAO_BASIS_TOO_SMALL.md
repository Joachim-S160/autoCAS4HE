# IBO MINAO Basis Too Small for Heavy Element Virtual Localization

## Status: OPEN BUG

**Date**: 2026-01-28
**Affects**: Po2, Bi2, and other heavy elements with `nOcc > nMINAO`
**Error**: `RuntimeError: The IBO localization basis is too small to localize the given orbital selection.`

---

## Context

The energy-based Rydberg cutoff (commit `6c6ed35` on `heavy-elements-support`) successfully fixed the old crash:
```
RuntimeError: A core orbital is assigned to be virtual. Something is wrong here!
```

However, a second error now surfaces — one that was previously masked by the first crash.

---

## What Happens

With the energy-based Rydberg cutoff (1.0 Ha for Po, Z=84):

1. Orbitals with eigenvalue > 1.0 Ha are flagged as Rydberg
2. For Po2, most virtual orbital eigenvalues are **below** 1.0 Ha (0.03, 0.11, 0.37, 0.44, 0.51 Ha etc.)
3. These low-energy virtuals are correctly classified as **valence virtual** (good for excited states!)
4. The valence virtual orbital indices go up to ~135 (the last basis function index)
5. IBO localization receives these indices and checks:
   ```cpp
   // IBOLocalization.cpp:76-77
   if (maxIndex > B2->getNBasisFunctions())
       throw SerenityError("The IBO localization basis is too small ...");
   ```
6. `B2` is the MINAO basis with only 26 functions for Po2
7. `maxIndex = 135 > 26` → **crash**

---

## Root Cause

The check at `IBOLocalization.cpp:76` compares the orbital index against the MINAO basis size. This is overly restrictive for virtual orbital localization because:

- Orbital indices are indices into the full basis (136 functions for Po2)
- The MINAO basis (26 functions for Po2) is a projection basis, not the orbital space
- The `replaceVirtuals` logic at lines 93-110 is specifically designed to handle the case where the IAO basis doesn't span the virtual valence orbital space — but the hard check on line 76 throws *before* that logic gets a chance to run

---

## Po2 Numbers

| Property | Value |
|----------|-------|
| nBasisFunctions | 136 |
| nMINAO (B2) | 26 |
| nOccupied | 84 |
| nVirtual | 52 |
| Virtual eigenvalue range | 0.03 – ~5.0 Ha |
| Virtuals with E < 1.0 Ha | ~10 (valence virtual) |
| Virtuals with E > 1.0 Ha | ~42 (Rydberg) |
| Max valence virtual index | ~94 |
| **Check**: 94 > 26? | **Yes → crash** |

---

## Proposed Fix

### Option A: Relax the check for virtual localization (recommended)

In `IBOLocalization.cpp:76-77`, only enforce the MINAO size check for occupied orbitals. When localizing virtuals, the `replaceVirtuals` logic (lines 93-110) already handles basis mismatch via `reconstructVirtualValenceOrbitalsInplace`:

```cpp
// BEFORE:
if (maxIndex > B2->getNBasisFunctions())
    throw SerenityError("The IBO localization basis is too small ...");

// AFTER:
if (maxIndex > B2->getNBasisFunctions() && !localizeVirtuals)
    throw SerenityError("The IBO localization basis is too small ...");
```

The `localizeVirtuals` flag is already computed at line 74-75 based on whether any orbital index exceeds `nOcc`. When `localizeVirtuals == true`, the code at lines 93-98 checks `iaosSpanOrbitals()` and if needed calls `reconstructVirtualValenceOrbitalsInplace()` to project virtuals onto the IAO basis before localization.

### Option B: Cap valence virtual range at nMINAO

In `LocalizationTask.cpp`, after `getVirtualValenceOrbitalIndices()`, limit the valence range to at most `nMINAO - nOcc` valence virtuals (the rest become Rydberg). This is more conservative but discards potentially useful valence virtuals.

### Option C: Expand MINAO for heavy elements

Add more shells to the Po MINAO definition in Serenity's basis set data. This is the cleanest fix long-term but requires careful testing of the MINAO completeness for each heavy element.

---

## How to Apply Option A

1. Edit `serenity/src/analysis/orbitalLocalization/IBOLocalization.cpp` line 76:
   ```cpp
   if (maxIndex > B2->getNBasisFunctions() && !localizeVirtuals)
   ```

2. Rebuild Serenity:
   ```bash
   cd serenity/build && cmake .. && make -j$(nproc)
   ```

3. Rerun the Po2 test:
   ```bash
   cd tests/autocas/external_scf/Po2_IBO_fix_test
   qsub po2_ibo_fix.pbs
   ```

4. If `replaceVirtuals` logic at line 93-98 handles it correctly, the localization should complete. If it still fails, the IAO projection itself may need adjustment (Option C).

---

## File References

| File | Line | Role |
|------|------|------|
| `serenity/src/analysis/orbitalLocalization/IBOLocalization.cpp` | 76-77 | **The check that throws** |
| `serenity/src/analysis/orbitalLocalization/IBOLocalization.cpp` | 93-110 | `replaceVirtuals` logic that handles IAO basis mismatch |
| `serenity/src/tasks/LocalizationTask.cpp` | 155-170 | Energy-based Rydberg cutoff (our fix, works correctly) |
| `serenity/src/data/OrbitalController.cpp` | 763-778 | `getVirtualValenceOrbitalIndices` — builds orbital ranges from flags |

---

## Relationship to Previous Fixes

| Fix | Commit | Result |
|-----|--------|--------|
| Cap nRydberg at nVirtuals | `c61b7dc` (rydberg-cap-experimental) | Fixed crash 1, caused crash 2 (zero valence virtuals) |
| Energy-based Rydberg cutoff | `6c6ed35` (heavy-elements-support) | Fixed crash 1, exposed crash 2 (MINAO basis too small) |
| **Relax IBOLocalization check** | **TODO** | Should fix crash 2 |

The energy-based cutoff is strictly better than the nRydberg cap — it preserves valence virtuals for excited state calculations. The remaining issue is just the overly strict sanity check in `IBOLocalization.cpp`.
