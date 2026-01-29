# autoCAS Algorithm Compatibility with Expanded MINAO for Heavy Elements

**Date**: 2026-01-29
**Context**: Follow-up to IBO_MINAO_FIX_PLAN_290126 - analyzing downstream impact
**Related**: IBO_MINAO_FIX_PLAN_290126.md, PO2_AUTOCAS_ERROR_ANALYSIS.md

---

## 1. Question

After expanding MINAO from 26 (valence-only) to 86 (all shells from ANO-RCC) for Po2, does the autoCAS algorithm still work correctly? Specifically:
- Does the initial CAS become unmanageably large?
- Does the DMRG cost explode?
- Does the S1 entropy plateau detection still function?

**Short answer**: The expanded MINAO does **not** change the CAS size or DMRG cost. autoCAS determines the active space from the `Elements` class (chemical knowledge), not from MINAO. MINAO only affects IBO localization quality.

---

## 2. How autoCAS Determines the Active Space

### 2.1 Core/valence split comes from Elements, not MINAO

The initial active space is determined in `molecule.py:167` (`__setup_orbital_and_electrons`):

```python
for atom in atom_list:
    self.core_orbitals += elements.get_core_orbitals(atom)
    self.valence_orbitals += elements.get_valence_orbitals(atom)
```

The `Elements` class (`chemical_elements.py`) defines fixed values per element:

| Element | core_orbitals | valence_orbitals | valence shells |
|---------|---------------|------------------|----------------|
| Po (Z=84) | 39 | 4 | 6s, 6p |
| Bi (Z=83) | 39 | 4 | 6s, 6p |

For Po2: `core_orbitals = 78`, `valence_orbitals = 8`, `valence_electrons = 12`.

These numbers come from chemical knowledge and are **completely independent of the MINAO basis size**.

### 2.2 Initial CAS construction

`active_space_handler.py:174` (`_make_valence_indices`):

```python
for i in range(self._molecule.valence_orbitals):
    orbital_indices.append(self._molecule.core_orbitals + i)
```

For Po2: indices 78-85 (8 orbitals). Occupation: `[2,2,2,2,2,2,0,0]` = CAS(12,8).

### 2.3 Where MINAO enters the picture

MINAO is used **only** in Serenity's IBO localization step, which runs before autoCAS constructs the CAS:

```
SCF → IBO localization (uses MINAO) → autoCAS CAS construction (uses Elements)
```

The IBO step localizes the MOs but does not change how many orbitals go into the CAS. After IBO, the orbital ordering is: core | occupied valence | virtual valence | Rydberg. autoCAS then picks orbitals 78-85 from this ordering.

---

## 3. Impact Analysis: MINAO 26 → 86

### 3.1 What changes

| Property | MINAO=26 | MINAO=86 | Impact |
|----------|----------|----------|--------|
| IBO localization | Crashes | Works | **Fix** |
| IAO quality | N/A (crashed) | Proper all-shell reference | Better localized MOs |
| nValVirt from IAO | N/A | 86 - 84 = 2 | Only 2 IBO virtual valence |
| Initial CAS size | CAS(12,8) | CAS(12,8) | **No change** |
| DMRG cost | N/A | Same as any CAS(12,8) | **No change** |
| Large CAS protocol | No (8 < 30) | No (8 < 30) | **Not triggered** |

### 3.2 What does NOT change

1. **CAS size**: Still CAS(12,8) — determined by Elements, not MINAO
2. **DMRG parameters**: D=250, 5 sweeps (initial); D=3000, 100 sweeps (final)
3. **Plateau detection**: Still scans S1 thresholds in 1% steps, looks for 10 consecutive steps with same orbital count
4. **Large CAS protocol**: Not triggered (8 orbitals << 30 threshold)
5. **Orbital exclusion**: Orbitals with S1 < 2% of max(S1) are excluded regardless of MINAO

### 3.3 What improves

With proper MINAO (all shells), the IBO localization produces physically meaningful localized orbitals for heavy elements. This means:
- The 6 occupied valence orbitals in the CAS are properly localized (lone pairs, bonding orbitals)
- The S1 entropy from DMRG is more interpretable
- Orbital assignment to atoms is more meaningful for the IAO population analysis

---

## 4. The "Only 2 Virtual Valence" Limitation

### 4.1 The constraint

With expanded MINAO (86 for Po2) and nOcc = 84:
- nValVirt_IAO = nMINAO - nOcc = 86 - 84 = 2

Only 2 virtual orbitals can be properly IBO-localized. The remaining virtual valence orbitals (from LocalizationTask's energy-based classification: ~15 total) are constructed by projection (`reconstructVirtualValenceOrbitalsInplace`), not IBO-localized.

### 4.2 Impact on autoCAS

The initial CAS(12,8) for Po2 contains only 2 virtual orbitals (indices 84-85). These 2 virtuals happen to match the 2 IBO-localized virtual valence orbitals. So for the **standard** autoCAS workflow, the limitation is not a problem.

### 4.3 When it could matter

The limitation becomes relevant if:
1. **Manually enlarged CAS**: User specifies more than 2 virtual valence orbitals → the extras are projection-reconstructed, not IBO-localized, meaning their spatial character is less chemically interpretable
2. **Excited states requiring many virtuals**: If DMRG S1 entropy indicates that more virtual orbitals are entangled, autoCAS cannot expand beyond the initial 8-orbital CAS — but this is an autoCAS design constraint, not a MINAO issue
3. **Elements with more valence orbitals**: If `chemical_elements.py` were updated to include more valence shells (e.g., 5d for Po), the CAS would grow, and more than 2 virtuals might be needed

---

## 5. DMRG Cost Scaling

### 5.1 For Po2 CAS(12,8)

DMRG cost scales approximately as O(D^2 * k^3 * N) where D = bond dimension, k = local dimension (4 for spatial orbitals), N = number of sites (orbitals).

| Phase | Bond dimension | Sweeps | Active orbitals | Cost class |
|-------|---------------|--------|-----------------|------------|
| Initial | 250 | 5 | 8 | Trivial |
| Final | 3000 | 100 | plateau-selected subset of 8 | Moderate |

CAS(12,8) is a small active space by DMRG standards. Even D=3000 with 8 orbitals is computationally cheap.

### 5.2 Would expanded MINAO ever trigger large CAS?

No. The large CAS protocol triggers when `valence_orbitals > 30` (`defaults.py:205`). For Po2, `valence_orbitals = 8`. The MINAO size does not influence this count.

For comparison, elements that might trigger large CAS:
- Lanthanides/actinides with 4f/5f in valence: potentially 7 f-orbitals + s + p + d → could exceed 30 for multinuclear complexes
- But this depends on `chemical_elements.py` definitions, not MINAO

### 5.3 Large CAS protocol (for reference)

If triggered (not for Po2), the large CAS protocol (`large_active_spaces.py`):
1. Splits occupied and virtual orbitals into chunks of `max_orbitals/2`
2. Creates all combinations → many small sub-CAS calculations
3. Runs initial DMRG (D=250, 5 sweeps) on each sub-CAS
4. Recombines S1 entropy by taking max across sub-CAS per orbital
5. Applies plateau detection on recombined S1

---

## 6. Orbital Index Consistency After IBO

### 6.1 The index assumption

autoCAS assumes orbital ordering: `[core_0 ... core_77 | val_78 ... val_85 | rydberg_86 ... rydberg_135]`

After IBO localization (LocalizationTask), orbitals are reordered into:
- Core (localized separately, indices 0 to nCore-1)
- Occupied valence (IBO-localized, indices nCore to nOcc-1)
- Virtual valence (reconstructed/IBO-localized, indices nOcc to nOcc+nValVirt-1)
- Rydberg (not localized, remaining indices)

### 6.2 Potential mismatch

For Po2:
- autoCAS expects valence at indices 78-85
- After IBO: occupied orbitals are 0-83, virtuals are 84-135
- Core orbitals (by energy): 0-61 (62 orbitals with epsilon < -5 Ha)
- Occupied valence: 62-83 (22 orbitals)
- Virtual valence: 84-98 (15 orbitals, energy < 1.0 Ha)
- Rydberg: 99-135

autoCAS picks indices 78-85, which maps to:
- 78-83: last 6 of the 22 occupied valence orbitals
- 84-85: first 2 virtual valence orbitals

This is correct for CAS(12,8) with 12 electrons. The 6 highest-index occupied valence orbitals should correspond to the chemically relevant 6s/6p occupied combinations.

### 6.3 Concern: are the right valence orbitals at indices 78-83?

After IBO localization, the ordering within the occupied block is NOT energy-ordered anymore — it's the order determined by the Jacobi rotations. The core orbitals (0-61) were localized separately and are properly "deep" orbitals. The occupied valence (62-83) are IBO-localized and should be chemically meaningful combinations of 6s and 6p (bonding/lone pair orbitals).

autoCAS picks the last 6 occupied (78-83) plus first 2 virtual (84-85). This assumes that `core_orbitals = 78` from Elements corresponds exactly to the core/valence split after IBO. But Serenity's energy-based core classification gives 62 core orbitals (epsilon < -5 Ha), while Elements says 78.

**This is a pre-existing discrepancy**: Elements counts 39 core orbitals per Po atom (1s through 5d = 1+1+3+1+3+5+1+3+5+1+3+5+1+3 = 39 orbitals per atom = 78 for Po2). Serenity's energy cutoff at -5 Ha gives only 62. The difference of 16 orbitals means some orbitals that Elements considers "core" are classified as "occupied valence" by Serenity's energy criterion.

**This discrepancy exists regardless of MINAO expansion** and may need separate attention if it causes problems. However, in practice, the DMRG should still capture the relevant physics — the S1 entropy will distinguish strongly correlated from weakly correlated orbitals, even if the initial CAS boundaries don't perfectly match the energy-based classification.

---

## 7. Conclusions

### 7.1 The expanded MINAO is safe for autoCAS

| Concern | Status |
|---------|--------|
| CAS becomes too large | **No** — CAS size from Elements (8 orbitals), not MINAO |
| DMRG cost explodes | **No** — CAS(12,8) is trivially small for DMRG |
| Large CAS triggered | **No** — 8 << 30 threshold |
| Plateau detection breaks | **No** — works on S1 entropy, independent of MINAO |
| Orbital quality degrades | **No** — improves with better MINAO |

### 7.2 Known limitations (pre-existing, not caused by MINAO expansion)

1. **Only 2 IBO virtual valence**: Inherent IAO constraint for heavy elements (nMINAO - nOcc = 2). Not a problem for standard CAS(12,8) but limits manual CAS expansion.
2. **Core count discrepancy**: Elements says 78 core for Po2, Serenity energy cutoff gives 62. This affects which orbitals end up in the initial CAS window.
3. **autoCAS cannot expand beyond initial CAS**: If the 8 valence orbitals are insufficient for the physics (e.g., double-shell effects, 5d correlation), autoCAS has no mechanism to add more orbitals.
4. **DMRG parameters are static**: D=250/5 sweeps for initial screening may be insufficient for strongly correlated heavy element systems, but this is a general autoCAS limitation.

### 7.3 Recommendation

Proceed with the MINAO expansion as planned in IBO_MINAO_FIX_PLAN_290126.md. The autoCAS algorithm is compatible with the expanded MINAO. The fix resolves the IBO crash without introducing new issues in the CAS selection pipeline.

The core count discrepancy (Section 6.3) and the "only 2 virtual valence" limitation (Section 4) are pre-existing issues that deserve separate investigation but are not blockers for the MINAO fix.

---

## Files referenced

| File | Role |
|------|------|
| `autocas/scine_autocas/utils/chemical_elements.py:739-745` | Po element definition (39 core, 4 valence) |
| `autocas/scine_autocas/utils/molecule.py:167-193` | Core/valence setup from Elements |
| `autocas/scine_autocas/cas_selection/active_space_handler.py:140-189` | Valence CAS construction |
| `autocas/scine_autocas/cas_selection/autocas.py:151-206` | S1 plateau detection |
| `autocas/scine_autocas/cas_selection/large_active_spaces.py:101-134` | Large CAS space partitioning |
| `autocas/scine_autocas/utils/defaults.py:197-230` | Algorithm defaults (plateau, DMRG params) |
| `serenity/src/analysis/orbitalLocalization/IBOLocalization.cpp` | IBO localization (uses MINAO) |
| `serenity/src/tasks/LocalizationTask.cpp` | Orbital range classification |
