# Research Document: IBO MINAO Basis Size Issue for Heavy Elements

**Date**: 2026-01-29
**Context**: Follow-up to SESSION_NOTES_280126 and IBO_MINAO_BASIS_TOO_SMALL bug report
**Related**: Knizia, JCTC 2013, 9(11), 4834-4843 (IAO/IBO paper)

---

## 1. Problem Statement

The IBO localization in Serenity crashes for heavy elements (Po, Bi, etc.) at IBOLocalization.cpp:76:
```cpp
if (maxIndex > B2->getNBasisFunctions())
    throw SerenityError("The IBO localization basis is too small ...");
```

For Po2: `maxIndex` (from orbitalRange, up to 135) > `B2->getNBasisFunctions()` (MINAO = 26) → crash.

---

## 2. Po2 Numbers

| Property | Value |
|----------|-------|
| nBasisFunctions (B1, ANO-RCC-VDZP) | 136 |
| nMINAO (B2, current) | 26 (13/atom) |
| nOcc (total) | 84 |
| Core orbitals (ε < -5 Ha) | 62 |
| Occupied valence | 22 |
| Virtual valence (energy-classified) | 15 |
| Rydberg (ε > 1.0 Ha) | 37 |

---

## 3. Why Knizia's Framework Requires nMINAO >= nOcc

**User note**: "Even in normal HF you have at most N MOs if you have a basis of N AOs. So if you project onto MINAO, MINAO needs to be as big or bigger. It sounds counterintuitive because you'd expect you'd project onto a smaller basis as to 'delocalize' but you also can't lose information during the process otherwise you get a different electronic configuration and you also really need all of the occupied orbitals."

**Analysis**: This understanding is correct. The IAO construction (paper eq 1) creates depolarized MOs by projecting occupied MOs onto MINAO:

```
|ĩ⟩ = P_B2 |i⟩  (projected onto MINAO and back)
```

In code (`IAOPopulationCalculator.cpp:241`):
```cpp
Eigen::MatrixXd tmp = P12 * P21 * C_spin.leftCols(nOccOrbs_spin);
```

This is a rank-limited projection. The result has at most rank = min(nMINAO, nOcc). If nMINAO < nOcc, some occupied MOs become linearly dependent after projection, and the subsequent symmetric orthogonalization (line 246: `es.operatorInverseSqrt()`) fails or produces degenerate results.

The point is not that MINAO is a "smaller" basis to lose information into — it's that the MINAO provides the reference atomic orbital space. The depolarized MOs must ALL be representable in this space, because the IAO construction then SPLITS the MINAO space into occupied and virtual-valence parts (eq 2). This split requires: dim(MINAO) = dim(occ) + dim(virt_valence), i.e., nMINAO = nOcc + nVirtValence.

---

## 4. Why the Check Uses Indices Instead of Counts

**User question**: "Why do we use the indices and don't we just look at the number of orbitals which is 22 for occ. valence and 15 for virt. valence, both under the current minimal basis space?"

The orbital indices from `orbitalRange` are used as DIRECT column indices into the CIAO matrix. In the Jacobi rotation loop (IBOLocalization.cpp:163):
```cpp
Qii += CIAO(mu, i) * CIAO(mu, i);  // i comes from orbitalRange
```

The CIAO matrix dimensions depend on the mode:
- **Occupied-only** (`withVirtuals=false`): CIAO shape = [nMINAO x nOcc] = [26 x 84]. Indices 62-83 ARE valid (84 columns exist).
- **With virtuals** (`withVirtuals=true`): CIAO shape = [nMINAO x nMINAO] = [26 x 26]. Indices >= 26 are out-of-bounds.

The check `maxIndex > B2->getNBasisFunctions()` compares against nMINAO (26), which is the correct bound only for the `withVirtuals=true` case. For occupied-only, the bound should be nOcc (84). The check is wrong for occupied localization — it compares against the wrong array dimension.

**User note**: "Both [22 occ valence + 15 virt valence] are under the current minimal basis space [26]. They fall out of the minimal basis space if combined [37 > 26], yet with the new ANO-RCC MINAO, they wouldn't."

This is correct as a count argument. But the deeper constraint is: nMINAO must exceed nOcc_total (not nOcc_valence), because the IAO construction projects ALL occupied MOs (core included) onto MINAO. The virtual valence count is limited to nMINAO - nOcc_total:
- Current: 26 - 84 = impossible
- Expanded: 86 - 84 = 2

---

## 5. The "Only 2 Virtual Valence" Problem

**User note**: "Only including 2 virtual valence orbitals still feels problematic."

With expanded MINAO (43/atom = 86 for Po2), the IAO framework supports:
- nValenceVirtuals = nMINAO - nOcc = 86 - 84 = 2

This is because 84 occupied MOs "consume" 84 of the 86 MINAO dimensions, leaving only 2 for virtual valence. For autoCAS excited state calculations, having only 2 localized virtual orbitals is likely insufficient.

**Root tension**: The IAO framework ties the virtual valence count to `nMINAO - nOcc_total`. Heavy elements have many core electrons that inflate nOcc, leaving almost no room for virtual valence in the MINAO space.

**Potential resolutions**:
1. Expand MINAO beyond minimal (add polarization functions like 7s, 7p) to increase nMINAO further. Deviates from Knizia's minimal basis concept.
2. Modify the IAO construction to exclude core from the projection (use nOcc_valence instead of nOcc_total). Would give nValVirt = 26 - 22 = 4 with current MINAO, or 86 - 22 = 64 with expanded MINAO. Requires careful validation that the IAO math still works when core MOs are excluded.
3. Use alternative localization software that handles this natively (see Section 8: ROSE).

---

## 6. Root Cause: MINAO Basis Regime Split

The MINAO file (`serenity/data/basis/MINAO`) has two regimes:

| Z range | Source | Content | nMINAO >= nOcc? |
|---------|--------|---------|-----------------|
| 1-36 (H-Kr) | cc-pVTZ contracted | ALL shells (core+valence) | Always |
| >= 39 (Y onwards) | Unknown source | Valence-only | Rarely |

For Po: MINAO has 2s + 2p + 1d = 13/atom (valence shells only). Missing: 1s, 2s, 2p, 3s, 3p, 3d, 4s, 4p, 4d, 4f, 5s, 5p core shells. The paper uses cc-pVTZ MINAO which includes all shells, but cc-pVTZ doesn't exist for Z > ~36.

---

## 7. Implementation Plan

### Step 1: Generate proper MINAO from ANO-RCC

The paper validates ANO-RCC as B2 (Table 1, footnote d). ANO-RCC exists in Serenity for all heavy elements. Extract the first N contracted functions per angular momentum (N = number of occupied shells per ℓ):

| Element | Config | Shells in MINAO | nMINAO/atom |
|---------|--------|-----------------|-------------|
| Y (Z=39) | [Kr]4d1 5s2 | 5s + 3p + 2d | 18 |
| Bi (Z=83) | [Xe]4f14 5d10 6s2 6p3 | 6s + 5p + 3d + 1f | 43 |
| Po (Z=84) | [Xe]4f14 5d10 6s2 6p4 | 6s + 5p + 3d + 1f | 43 |

**New file**: `scripts/generate_heavy_MINAO.py`
**Modified file**: `serenity/data/basis/MINAO`

### Step 2: Fix IBOLocalization.cpp:76 check

```cpp
// BEFORE:
if (maxIndex > B2->getNBasisFunctions())
    throw SerenityError("The IBO localization basis is too small ...");

// AFTER:
if (localizeVirtuals && maxIndex >= B2->getNBasisFunctions())
    throw SerenityError("The IBO localization basis is too small ...");
```

Only needed for virtual mode (CIAO has nMINAO cols). For occupied mode, CIAO has nOcc cols.

**File**: `serenity/src/analysis/orbitalLocalization/IBOLocalization.cpp:76`

### Step 3: Guard reconstruction against nOcc >= nMINAO

In `IAOPopulationCalculator.cpp`, inside `reconstructVirtualValenceOrbitalsInplace` at line 192, after `const unsigned int nOcc = occIAO.cols()`:

```cpp
if (nIAOBasisFunctions <= nOcc) {
    // MINAO too small for virtual valence. Only construct diffuse virtuals.
    const unsigned int nAllVirtuals = nBasisFunctions - nOcc;
    const Eigen::MatrixXd cOcc = C_spin.leftCols(nOcc);
    const Eigen::MatrixXd proj =
        Eigen::MatrixXd::Identity(nBasisFunctions, nBasisFunctions) - cOcc * cOcc.transpose() * S1;
    const Eigen::MatrixXd sDD = proj.transpose() * S1 * proj;
    Eigen::SelfAdjointEigenSolver<Eigen::MatrixXd> es(sDD);
    const unsigned int nAllVirt = nBasisFunctions - nOcc;
    const Eigen::MatrixXd u = es.eigenvectors().rightCols(nAllVirt);
    const Eigen::VectorXd eps = es.eigenvalues().tail(nAllVirt);
    const Eigen::VectorXd invEps = eps.array().inverse().sqrt().eval();
    C_spin.rightCols(nAllVirt) = (proj * u.leftCols(nAllVirt) * invEps.asDiagonal()).eval();
    continue;
}
```

**File**: `serenity/src/analysis/populationAnalysis/IAOPopulationCalculator.cpp:192`

### Step 4: Remap orbitalRange after reconstruction

After reconstruction in IBOLocalization.cpp (after line 110), virtual valence orbitals move to columns nOcc..nOcc+nValVirt-1. The pre-reconstruction orbitalRange becomes invalid. Add remapping:

```cpp
if (replaceVirtBeforeLoc) {
    const unsigned int nIAOBasis = B2->getNBasisFunctions();
    for_spin(orbitalRange, nOcc) {
        if (nIAOBasis > nOcc_spin) {
            const unsigned int nValVirt = nIAOBasis - nOcc_spin;
            std::vector<unsigned int> newRange;
            for (auto idx : orbitalRange_spin) {
                if (idx < nOcc_spin)
                    newRange.push_back(idx);
            }
            for (unsigned int v = 0; v < nValVirt; ++v)
                newRange.push_back(nOcc_spin + v);
            orbitalRange_spin = newRange;
        }
    };
}
```

**File**: `serenity/src/analysis/orbitalLocalization/IBOLocalization.cpp` (after line 110)

### Step 5: Rebuild and test

1. `cd serenity/build && cmake .. && make -j$(nproc)`
2. `cd serenity/build && ctest`
3. Po2 test, Bi2 test
4. Light element regression (N2, CH4)

---

## 8. Future: ROSE Software (Senjean et al.)

**User note**: After implementing this fix, investigate whether ROSE (by Bruno Senjean et al.) is a better alternative to Serenity for IAO/IBO, potentially interfaceable with PySCF.

**Reference**: Senjean, Sen, Repisky, Knizia, Visscher, JCTC 2021, 17, 1337
**Repository**: https://gitlab.com/quantum_rose/rose

Key questions investigated (see AUTOCAS_EXPANDED_MINAO_COMPATIBILITY.md Section 10 for full analysis):

| Question | Answer |
|----------|--------|
| Does ROSE handle heavy elements natively? | Likely yes — constructs MINAO internally |
| Does ROSE handle nMINAO < nOcc? | Likely yes — "spanning the occupied space exactly" |
| Does ROSE support quaternion spinors? | Yes, via DIRAC interface |
| Can ROSE interface with PySCF? | Yes — non-relativistic + scalar-X2C |
| OpenMolcas interface? | **No** — not supported |

**User note**: "I don't see many good options to using ROSE; autoCAS can be interfaced with PySCF, but ROSE's PySCF interface only works for non-relativistic and scalar-X2C orbitals using cartesian functions. I currently use OpenMolcas's DKH2 in the SCF. Although wait OpenMolcas can also do X2C, perhaps this is not an issue."

**Assessment**: The most viable path is PySCF with scalar-X2C (similar physics to DKH2). ROSE has no OpenMolcas interface, so switching OpenMolcas's Hamiltonian to X2C doesn't help directly. However, running the SCF in PySCF with scalar-X2C instead of OpenMolcas with DKH2 would enable the ROSE integration. This is a medium-term effort.

---

## Files to modify

| File | Change |
|------|--------|
| `serenity/data/basis/MINAO` | Expand heavy element entries from ANO-RCC |
| `serenity/src/analysis/orbitalLocalization/IBOLocalization.cpp` | Fix line 76 check + orbitalRange remapping |
| `serenity/src/analysis/populationAnalysis/IAOPopulationCalculator.cpp` | Guard nOcc >= nMINAO |
| New: `scripts/generate_heavy_MINAO.py` | MINAO generation from ANO-RCC |
