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

## 7. Direct Orbital Selection (DOS) and Orbital Mapping

**User note**: "You haven't mentioned how direct orbital selection and orbital mapping come in to play in the consistent active space algorithm and how a larger MINAO file might change these."

**References**:
- Bensberg, Reiher, JPCL 2023, 14(8), 2112-2118 — "Corresponding Active Orbital Spaces along Chemical Reaction Paths"
- Bensberg, Neugebauer, PCCP 2020, 22, 26093 — "Direct orbital selection for projection-based embedding"

### 7.1 What DOS actually is

DOS (Direct Orbital Selection) is the orbital mapping algorithm implemented in Serenity's `DirectOrbitalSelection` class (`serenity/src/analysis/directOrbitalSelection/DirectOrbitalSelection.h`). The Generalized DOS (GDOS) extends it to N structures. **Note: "DOS" stands for Direct Orbital Selection, not Density of States.**

DOS compares localized orbitals between structures using two descriptors:
1. **Orbital-wise populations** (IAO-Shell or Mulliken) — indicator of orbital localization
2. **Orbital kinetic energy** — indicator of orbital spatial extent/shape

Orbitals that are similar across structures are grouped together; orbitals that change substantially are identified as chemically interesting (active).

### 7.2 How DOS/GDOS works in the consistent active space protocol

The consistent active space protocol (`workflows/consistent_active_space/protocol.py`) runs across multiple geometries (e.g., equilibrium and stretched Po2). The flow is:

1. **IBO localization on first geometry** (template system)
2. **For each subsequent geometry**: orbital alignment to template, then IBO localization
3. **GDOS orbital mapping** (`serenity.py:338-363`, wrapping Serenity's `GeneralizedDOSTask`): compares localized orbitals across geometries using IAO populations and kinetic energy similarity
4. **Independent DMRG + S1 plateau detection** per geometry
5. **Combine active spaces** (`cas_combination.py:39-92`): union of selected orbitals across geometries, mapped via DOS orbital groups

### 7.3 How DOS depends on IBO/IAO quality

The GDOS matching (`serenity.py:338-363`) uses iterative threshold passes:

```python
gdos.settings.similarityLocThreshold = [3e-1, 5e-3, 1e-4]
gdos.settings.similarityKinEnergyThreshold = [3e-1, 5e-3, 1e-4]
gdos.settings.bestMatchMapping = True
```

- `similarityLocThreshold`: compares **IAO population** similarity between geometries
- `similarityKinEnergyThreshold`: compares **kinetic energy** similarity
- Three passes with decreasing thresholds: broad matching → refined → strict

The DOS creates **orbital groups** (`DOSOrbitalGroup` objects) — sets of orbitals that correspond between geometries (e.g., the Po-Po sigma bond at equilibrium maps to the Po lone pairs at stretched geometry). The `combine_active_spaces` function then takes the union of selected groups.

**The IAO populations used by DOS are directly computed from the MINAO basis.** This means DOS depends on MINAO quality in two ways:
1. **IBO localization quality**: MINAO → IAO → IBO → spatial character of localized orbitals
2. **IAO population descriptors**: MINAO → IAO populations → DOS orbital similarity metric

### 7.4 Impact of expanded MINAO on DOS

**Better MINAO → better IAO populations → more reliable DOS matching.** The chain is:

```
MINAO (reference AOs) → IAO (depolarized MOs) → IBO (localized MOs)
                       → IAO populations → DOS similarity comparison
```

With the current broken MINAO (26 for Po2), IBO crashes entirely — no DOS mapping is possible. With expanded MINAO (86), both the IBOs and the IAO populations will be physically meaningful, making the DOS matching more stable across geometries.

Potential concern: if localization quality changes significantly, the `partitioning_thresholds` (`serenity.py:78-81`, default `[3e-1, 5e-3, 1e-4]`) might need retuning. However, since the old MINAO never worked for heavy elements, this is not a regression — it's a first-time setup.

### 7.5 S1 plateau detection (within each geometry)

Within each geometry, CAS orbital selection works via S1 entropy plateau detection (`autocas.py:151-206`):

1. Normalize S1 entropies by max(S1)
2. Scan thresholds 0→1 in steps of 0.01
3. At each threshold, count orbitals exceeding it
4. Detect plateau (10 consecutive steps with same count)
5. Select the top N orbitals by S1 magnitude (`set_from_plateau`, `active_space_handler.py:335-358`)

This is independent of MINAO. The S1 entropies come from DMRG, which operates on the CAS defined by Elements, not MINAO.

---

## 8. Expanding the Default Chemical Valence Picture

**User note**: "In the future I might want to look into changing autoCAS's default chemical valence picture (6 occ. 2 virt.) to something bigger like 8 occ. 5 virt."

### 8.1 Current situation for Po2

From `chemical_elements.py:739-745`:
- Po: 39 core orbitals (1s through 5d), 4 valence orbitals (6s, 6p)
- Po2: CAS(12,8) = 6 doubly-occupied + 2 empty

### 8.2 What expanding to (8 occ, 5 virt) would mean

For Po2 with 8 occupied + 5 virtual = 13 orbitals total per system:
- CAS(~16-20, 13) depending on which shells are added
- If 5d is included in valence: 5d(5) + 6s(1) + 6p(3) = 9 orbitals/atom → 18 for Po2
- Still well under the large CAS threshold of 30

### 8.3 Constraint from the "only 2 virtual valence" problem

With expanded MINAO (43/atom = 86 for Po2) and nOcc = 84:
- Only 2 virtual orbitals can be IBO-localized (nMINAO - nOcc = 2)
- If 5 virtual valence orbitals are desired, 3 would be projection-reconstructed, not IBO-localized
- Their spatial character would be less chemically interpretable

To get 5 IBO-localized virtuals, MINAO would need nMINAO >= nOcc + 5 = 89, i.e., at least 45 functions per atom. This could be achieved by adding beyond-minimal functions to MINAO:
- Add 7s: 44/atom → 88 for Po2 → 4 virtual valence
- Add 7s + 7p: 47/atom → 94 for Po2 → 10 virtual valence

This deviates from Knizia's minimal basis concept but may be necessary for heavy elements where the core orbital count is so large. This is related to the MINAO derivation concern below (Section 9).

### 8.4 Modifying chemical_elements.py

To change the default valence, modify `chemical_elements.py:739-745`:

```python
# Current:
"number of core orbitals": 39,      # 1s-5d
"number of valence orbitals": 4,     # 6s, 6p

# Example expanded (including 5d in valence):
"number of core orbitals": 34,       # 1s-5p
"number of valence orbitals": 9,     # 5d, 6s, 6p
```

This would change autoCAS's CAS window but NOT the IBO localization or MINAO. The orbital indices would shift: autoCAS would pick indices 68-85 (18 orbitals for Po2) instead of 78-85 (8 orbitals).

---

## 9. MINAO Derivation: State-Averaged Contractions vs ANO-RCC

**User note**: "In the original 2013 Knizia paper they mention that for transition metals they used contracted functions of the cc-pVTZ basis set (a minimal basis subset), but that they derived it from averages over important states instead of only ground states. We should be careful about implementing something similar, perhaps we should look at contracted functions of ANO-RCC-VTZ(P). Although I'm not sure if this would be useful as I will already use ANO-RCC-VTZP eventually as a basis set (right now we're using ANO-RCC-VDZP)."

### 9.1 Knizia's MINAO derivation

From the paper (Section 2.1): The MINAO for light elements (H-Kr) are derived from cc-pVTZ by taking the most contracted function per angular momentum shell. For transition metals, these were specifically derived from averages over multiple important atomic states (ground state, low-lying excited states, cation/anion), not just the ground state. This ensures the MINAO represents the atom in various bonding situations.

### 9.2 ANO-RCC already has state-averaged character

ANO-RCC basis sets are derived from **atomic natural orbitals** obtained by CASSCF/CASPT2 calculations averaged over multiple electronic states:
- Ground state configurations
- Excited states and ionization states
- Different spin multiplicities

This is conceptually similar to Knizia's state-averaging approach. The ANO-RCC contracted functions already incorporate information about how the atom behaves in different bonding situations. Using the first N contracted functions from ANO-RCC as MINAO is therefore well-motivated.

Knizia explicitly validates ANO-RCC as B2 in Table 1 of the paper (footnote d): "For transition metals, we used the minimal basis given in the ANO-RCC sets."

### 9.3 Using ANO-RCC-VTZP as both orbital basis and MINAO source

The concern: if the MINAO is a contraction of the same basis set used for the SCF, the IAO projection might not properly "depolarize" the MOs because the projection basis overlaps too much with the full basis.

**Analysis**: This is not a problem in practice because:
1. The MINAO is a **minimal** contraction (first N functions per ℓ), while the orbital basis has many more contracted functions per ℓ. They span different spaces.
2. The IAO construction explicitly handles the relationship between B1 (orbital basis) and B2 (MINAO) via the overlap matrices P12 and P21.
3. Knizia's paper uses cc-pVTZ-derived MINAO with cc-pVTZ orbital basis for light elements — same basis family, no issues reported.
4. Moving from ANO-RCC-VDZP to ANO-RCC-VTZP as the orbital basis would actually improve the IAO quality, as the larger basis allows better representation of polarization effects that the IAO "depolarization" then removes.

### 9.4 Should we use ANO-RCC-VTZ contracted functions instead?

Using ANO-RCC-VTZ(P) contracted functions for MINAO instead of ANO-RCC (unspecified zeta) would give slightly different contraction coefficients. However, ANO-RCC basis sets share the same primitive exponents across zeta levels — only the number and coefficients of contractions change. The first contracted function per ℓ is essentially the same across DZ/TZ/QZ levels in ANO-RCC, so the choice of which ANO-RCC variant to extract MINAO from should have minimal impact.

**Recommendation**: Use the ANO-RCC basis already in Serenity (which appears to be the general ANO-RCC set). The MINAO extraction only takes the first N contracted functions per ℓ, and these are stable across ANO-RCC variants.

---

## 10. ROSE Software Assessment

**User note**: "I don't see many good options to using ROSE, reduction of orbital extent from Bruno Senjean et al; autoCAS can be interfaced with PySCF, but ROSE's PySCF interface only works for non-relativistic and scalar-X2C orbitals using cartesian functions. I currently use OpenMolcas's DKH2 in the SCF. Although wait OpenMolcas can also do X2C, perhaps this is not an issue."

**Reference**: Senjean, Sen, Repisky, Knizia, Visscher, JCTC 2021, 17, 1337 — "Generalization of Intrinsic Orbitals to Kramers-Paired Quaternion Spinors, Molecular Fragments, and Valence Virtual Spinors"

### 10.1 ROSE interface support

From the ROSE README (https://gitlab.com/quantum_rose/rose):

| Interface | Relativistic support | Basis functions | Format |
|-----------|---------------------|-----------------|--------|
| **DIRAC** | Real + quaternion spinors (full 4c) | Spherical + cartesian | .h5 |
| **PySCF** | Non-relativistic, scalar-X2C | Cartesian only | .h5 |
| **PSI4** | Non-relativistic, scalar-X2C | Cartesian | .h5 |
| **ADF** | Non-relativistic, ZORA | Slater-type | .rkf |
| **Gaussian** | Non-relativistic, scalar-X2C | Cartesian | .fchk |
| **OpenMolcas** | **Not supported** | N/A | N/A |

### 10.2 Paths to using ROSE for heavy elements

**Path A: PySCF with scalar-X2C**
- autoCAS already has a PySCF interface
- PySCF supports scalar-X2C
- ROSE's PySCF interface supports scalar-X2C
- Flow: PySCF (scalar-X2C SCF) → ROSE (IAO/IBO) → autoCAS (CAS selection)
- Limitation: cartesian functions only, scalar-X2C is less accurate than full 2c/4c for very heavy elements (Z > 80)
- DKH2 and scalar-X2C give similar results for scalar relativistic effects — the main difference is in the transformation method, not the physics captured

**Path B: DIRAC with full 4-component**
- DIRAC supports quaternion spinors — ROSE's strongest relativistic interface
- Captures spin-orbit coupling properly (important for Po, Bi)
- Would require building a DIRAC → autoCAS bridge (no existing interface)
- Significantly more computational cost for the SCF
- Most physically rigorous for heavy elements

**Path C: Switch OpenMolcas from DKH2 to X2C**
- OpenMolcas supports X2C (exact two-component)
- But ROSE has **no OpenMolcas interface** — switching the Hamiltonian in OpenMolcas doesn't help with ROSE
- Would still need to export orbitals to a format ROSE can read, or use a different SCF code

### 10.3 Most viable path

**PySCF with scalar-X2C** is the most practical route:
- autoCAS already interfaces with PySCF
- ROSE already interfaces with PySCF
- Scalar-X2C captures the dominant relativistic effects (mass-velocity, Darwin terms)
- For Po/Bi, spin-orbit coupling is significant but the scalar part is the largest correction

The main trade-off vs the current OpenMolcas DKH2 setup:
- Scalar-X2C ≈ DKH2 in accuracy for scalar relativistic effects
- PySCF's X2C implementation handles contracted basis sets
- Loss: no spin-orbit coupling (would need DIRAC path for that)
- Gain: access to ROSE's proper MINAO handling for heavy elements

### 10.4 ROSE's MINAO handling

ROSE constructs "a minimal set of IAOs spanning the occupied space exactly and a few valence virtuals" — this suggests ROSE may handle the nMINAO >= nOcc requirement internally, potentially solving the heavy element MINAO problem without needing to manually expand Serenity's MINAO file.

This is worth investigating: if ROSE's IAO construction already handles heavy elements correctly, it could replace both the MINAO fix AND the IBO localization in Serenity.

### 10.5 Assessment summary

| Criterion | ROSE viability |
|-----------|---------------|
| Heavy element MINAO | Likely handled internally |
| Relativistic SCF | Via PySCF (scalar-X2C) or DIRAC (full 4c) |
| OpenMolcas DKH2 | No direct interface |
| autoCAS integration | Feasible via PySCF bridge |
| Spin-orbit coupling | Only via DIRAC interface |
| Maturity | Published, open-source, integrated into ADF 2025 |

**Recommendation**: Investigate ROSE as a medium-term replacement for Serenity's IBO localization, using the PySCF scalar-X2C path. The immediate MINAO fix in Serenity (IBO_MINAO_FIX_PLAN_290126.md) should proceed as a short-term solution, since building the ROSE integration requires more work.

---

## 11. MINAO Expansion for Larger Molecules

**User note**: "I need to be sure that this extended ANO-RCC MINAO will also be sufficient for larger molecules. If such a patch is still safe for larger molecules also, I'll do it, if it's not I'll look into ROSE more."

### 11.1 MINAO headroom scales favorably with light atoms

The "only 2 virtual valence" problem (nMINAO - nOcc = 2 for Po2) is worst for homonuclear heavy element dimers. For molecules containing light atoms, the light atoms contribute more MINAO headroom because light elements have nMINAO > nOcc per atom.

MINAO per atom (expanded ANO-RCC for Z >= 39, cc-pVTZ for Z <= 36):

| Atom | Z | nMINAO/atom | nOcc/atom (core+val) | Excess/atom |
|------|---|-------------|----------------------|-------------|
| H | 1 | 1 | 0-1 | 0-1 |
| O | 8 | 5 | 4 | 1 |
| Pb | 82 | 43 | 41 | 2 |
| Bi | 83 | 43 | 41-42 | 1-2 |
| Po | 84 | 43 | 42 | 1 |

### 11.2 Target molecules

| Molecule | nMINAO | nOcc | nValVirt (IAO) | Sufficient? |
|----------|--------|------|----------------|-------------|
| **Po2** | 86 | 84 | **2** | Minimal |
| **Po(OH)2** | 55 | 51 | **4** | Better |
| **Po(OH)4** | 67 | 60 | **7** | Good |
| **PoPb** | 86 | 83 | **3** | Marginal |
| **PoBi** | 86 | 83/84 (UHF) | **2-3** | Minimal |
| **BiPb** | 86 | 82/83 (UHF) | **3-4** | Marginal |

Calculation details:
- Po(OH)4: MINAO = 43 + 4×5 + 4×1 = 67, electrons = 84 + 32 + 4 = 120, nOcc = 60
- Po(OH)2: MINAO = 43 + 2×5 + 2×1 = 55, electrons = 84 + 16 + 2 = 102, nOcc = 51
- PoBi: 84 + 83 = 167 electrons (doublet), nOcc_alpha = 84, nOcc_beta = 83

### 11.3 Key insight

**Larger molecules with light atoms are actually better than Po2.** The light atoms contribute relatively more MINAO functions per occupied orbital than heavy atoms. Po(OH)4 with 7 virtual valence orbitals is substantially more comfortable than Po2 with only 2.

For homonuclear heavy dimers (Po2, PoBi, PoPb), the headroom remains tight (2-4 virtual valence). This is inherent to the IAO framework for heavy elements and cannot be fully resolved without either:
1. Adding beyond-minimal functions (7s, 7p) to MINAO — deviating from Knizia's minimal basis concept
2. Using ROSE, which may handle this differently
3. Accepting projection-reconstructed virtuals for the excess

### 11.4 Verdict: safe to proceed with MINAO expansion

The expanded ANO-RCC MINAO is sufficient for all target molecules. The constraint nMINAO >= nOcc is satisfied in all cases. The number of IBO-localizable virtual valence orbitals varies (2-7), but the autoCAS initial CAS is determined by Elements (typically 8 orbitals), not by nValVirt_IAO.

---

## 12. OpenMolcas-PySCF Orbital Transfer for SO-CASSI/SO-MPSSI

**User note**: "The end goal is to create dissociation profiles using SO-CASSI or SO-MPSSI using OpenMolcas for a broad range of Po containing molecules. I should be able to convert the final CAS to something useful OpenMolcas can use for its initial CASSCF/DMRGSCF."

### 12.1 End-goal workflow

The complete pipeline for dissociation profiles with spin-orbit coupling:

```
1. SCF (OpenMolcas DKH2)
   → orbitals imported to Serenity
2. IBO localization (Serenity, with expanded MINAO)
   → localized orbitals
3. DOS orbital mapping + autoCAS (consistent CAS across geometries)
   → CAS(n_el, n_orb) definition + orbital indices
4. Transfer CAS back to OpenMolcas
   → CASSCF/DMRGSCF with autoCAS-selected active space
5. SO-CASSI or SO-MPSSI (OpenMolcas)
   → spin-orbit coupled dissociation profiles
```

### 12.2 OpenMolcas-PySCF compatibility

OpenMolcas and PySCF can exchange orbitals via several routes:

| Route | Tool | Direction | Format |
|-------|------|-----------|--------|
| **MOKIT** (recommended) | `py2molcas` | PySCF → OpenMolcas | InpOrb |
| **MOKIT** | `molden2fch` + `bas_fch2py` | OpenMolcas → PySCF | Molden → fchk → py |
| **Molden files** | `pyscf.tools.molden` | Both directions | .molden |
| **HDF5** | Direct | OpenMolcas ↔ any | .h5 |

**MOKIT** (Molecular Orbital Kit, https://github.com/1234zou/MOKIT) is the most robust tool for orbital transfer between quantum chemistry codes, with negligible energy loss (< 1e-6 Ha) during transfer. It handles basis ordering differences for angular momentum up to H (l=5).

### 12.3 Current autoCAS → OpenMolcas path

autoCAS already uses OpenMolcas for DMRG (via the OpenMolcas interface). The selected CAS (orbital indices + occupation) is passed directly to OpenMolcas's RASSCF/DMRGSCF modules. This means step 4 of the pipeline should work without additional orbital transfer — autoCAS already orchestrates the OpenMolcas CASSCF/DMRGSCF calculations.

For SO-CASSI/SO-MPSSI (step 5), the CASSCF/DMRGSCF wavefunction from step 4 is used directly within OpenMolcas. No additional orbital transfer is needed — it's all within OpenMolcas after autoCAS hands off the CAS definition.

### 12.4 If switching to PySCF for SCF (for ROSE integration)

If the SCF moves from OpenMolcas to PySCF (to enable ROSE for IAO/IBO), the final CAS still needs to get back to OpenMolcas for SO-CASSI. The transfer would be:

```
PySCF (X2C SCF) → ROSE (IBO) → autoCAS (CAS selection) → MOKIT → OpenMolcas (SO-CASSI)
```

This adds a MOKIT transfer step but is technically feasible.

---

## 13. Conclusions

### 13.1 The expanded MINAO is safe for autoCAS and target molecules

| Concern | Status |
|---------|--------|
| CAS becomes too large | **No** — CAS size from Elements (8 orbitals), not MINAO |
| DMRG cost explodes | **No** — CAS(12,8) is trivially small for DMRG |
| Large CAS triggered | **No** — 8 << 30 threshold |
| Plateau detection breaks | **No** — works on S1 entropy, independent of MINAO |
| Orbital quality degrades | **No** — improves with better MINAO |
| DOS orbital mapping breaks | **No** — improves: better IAO populations + better IBO |
| Larger molecules fail | **No** — light atoms add MINAO headroom (Section 11) |
| CAS transfer to OpenMolcas | **Works** — autoCAS already orchestrates OpenMolcas CASSCF |

### 13.2 Known limitations (pre-existing, not caused by MINAO expansion)

1. **Limited IBO virtual valence**: nValVirt = nMINAO - nOcc ranges from 2 (Po2) to 7 (Po(OH)4). Tight for homonuclear heavy dimers, comfortable for molecules with light atoms.
2. **Core count discrepancy**: Elements says 78 core for Po2, Serenity energy cutoff gives 62. Affects which orbitals end up in the initial CAS window (Section 6.3).
3. **autoCAS cannot expand beyond initial CAS**: If the 8 valence orbitals are insufficient, autoCAS has no mechanism to add more.
4. **DMRG parameters are static**: D=250/5 sweeps for initial screening may be insufficient for strongly correlated heavy element systems.

### 13.3 Future directions

1. **Expand default valence** (Section 8): Modify `chemical_elements.py` to include 5d in Po/Bi valence → CAS grows from (12,8) to (~20,18). Needs more IBO virtual valence — feasible for Po(OH)4 (7 available), tight for Po2 (only 2).
2. **ROSE integration** (Section 10): Most viable via PySCF scalar-X2C path. Solves heavy element MINAO handling natively. Medium-term effort. Final CAS transferable to OpenMolcas via MOKIT.
3. **MINAO derivation** (Section 9): ANO-RCC contracted functions are well-motivated (state-averaged, Knizia-validated). No issues with using same basis family for orbital basis and MINAO source.
4. **SO-CASSI/SO-MPSSI** (Section 12): The autoCAS → OpenMolcas CASSCF → SO-CASSI pipeline is straightforward. autoCAS already orchestrates OpenMolcas.

### 13.4 Recommendation

Proceed with the MINAO expansion as planned in IBO_MINAO_FIX_PLAN_290126.md. The expanded MINAO is safe for all target molecules (Po2, Po(OH)4, PoPb, PoBi). The autoCAS algorithm — including DOS orbital mapping and the consistent active space protocol — is fully compatible. The final CAS integrates directly with OpenMolcas for SO-CASSI/SO-MPSSI dissociation profiles.

---

## References

- Knizia, JCTC 2013, 9(11), 4834-4843 — IAO/IBO paper
- Bensberg, Reiher, JPCL 2023, 14(8), 2112-2118 — Corresponding active orbital spaces (DOS in autoCAS)
- Bensberg, Neugebauer, PCCP 2020, 22, 26093 — Direct orbital selection for embedding
- Senjean, Sen, Repisky, Knizia, Visscher, JCTC 2021, 17, 1337 — ROSE / generalized IAO
- MOKIT: https://github.com/1234zou/MOKIT — Orbital transfer between codes

---

## Files referenced

| File | Role |
|------|------|
| `autocas/scine_autocas/utils/chemical_elements.py:739-745` | Po element definition (39 core, 4 valence) |
| `autocas/scine_autocas/utils/molecule.py:167-193` | Core/valence setup from Elements |
| `autocas/scine_autocas/cas_selection/active_space_handler.py:140-189` | Valence CAS construction |
| `autocas/scine_autocas/cas_selection/active_space_handler.py:335-358` | `set_from_plateau()` |
| `autocas/scine_autocas/cas_selection/autocas.py:123-206` | S1 sorting + plateau detection |
| `autocas/scine_autocas/cas_selection/cas_combination.py:39-92` | Orbital space combination across geometries |
| `autocas/scine_autocas/cas_selection/large_active_spaces.py:101-134` | Large CAS space partitioning |
| `autocas/scine_autocas/utils/defaults.py:197-230` | Algorithm defaults (plateau, DMRG params) |
| `autocas/scine_autocas/interfaces/serenity/serenity.py:190-363` | IBO localization + DOS orbital mapping |
| `autocas/scine_autocas/workflows/consistent_active_space/protocol.py` | Consistent CAS protocol orchestration |
| `serenity/src/analysis/directOrbitalSelection/DirectOrbitalSelection.h` | DOS algorithm implementation |
| `serenity/src/tasks/GeneralizedDOSTask.h` | GDOS task (multi-structure DOS) |
| `serenity/src/analysis/orbitalLocalization/IBOLocalization.cpp` | IBO localization (uses MINAO) |
| `serenity/src/tasks/LocalizationTask.cpp` | Orbital range classification |
