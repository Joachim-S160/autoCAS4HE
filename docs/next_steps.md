# Next Steps: Heavy Element autoCAS Development

**Created**: 2026-01-27
**Status**: Active

---

## Priority 1: Revert Rydberg Overflow Patch

### Problem with Current Patch
The patch in `LocalizationTask.cpp` that caps `nRydbergOrbitals` at `nVirtuals` causes **all virtual orbitals to be classified as Rydberg**, leaving **zero valence virtuals**. This defeats the purpose of IBO localization which needs valence virtuals to form proper bond orbitals.

### Action
- [x] Move the Rydberg overflow patch to a separate branch (`rydberg-cap-experimental`)
- [x] Keep `heavy-elements-support` branch without this patch
- [ ] Document this as a known issue with IBO for heavy elements

### Branch Structure
```
main
├── heavy-elements-support (working branch - NO Rydberg cap patch)
└── rydberg-cap-experimental (contains the cap patch for reference)
```

---

## Priority 2: Test Alternative Localization Methods

Since IBO has fundamental issues with heavy elements (small MINAO → Rydberg overflow), we need to test other localization methods available in autoCAS/Serenity.

### CLI Option Added
A new `-L/--localization` flag was added to `scine_autocas_consistent_active_space`:

```bash
scine_autocas_consistent_active_space -e -o "orb1.h5,orb2.h5" -L PIPEK_MEZEY -b ANO-RCC-VDZP mol1.xyz mol2.xyz
```

### Available Localization Methods
| Method | CLI Flag | Description | MINAO Required? |
|--------|----------|-------------|-----------------|
| IBO | `-L IBO` | Intrinsic Bond Orbitals (default) | Yes - fails for Po2 |
| Pipek-Mezey | `-L PIPEK_MEZEY` | Mulliken population localization | No |
| Foster-Boys | `-L BOYS` | Spatial extent minimization | No |
| Edmiston-Ruedenberg | `-L EDMINSTON_RUEDENBERG` | Coulomb self-repulsion maximization | No |

### Test Folders Created
```
tests/autocas/localization_methods/
├── Po2_PM/          # Pipek-Mezey test
│   ├── po2_pm.pbs   # PBS job script
│   ├── po2_0.xyz, po2_1.xyz
│   └── po2_0.scf.h5, po2_1.scf.h5
├── Po2_FB/          # Foster-Boys test
│   ├── po2_fb.pbs   # PBS job script
│   ├── po2_0.xyz, po2_1.xyz
│   └── po2_0.scf.h5, po2_1.scf.h5
└── README.md
```

### How to Run
```bash
cd tests/autocas/localization_methods/Po2_PM && qsub po2_pm.pbs
cd tests/autocas/localization_methods/Po2_FB && qsub po2_fb.pbs
```

### Status
- [x] Add `-L` CLI option to autoCAS
- [x] Create PM test directory and PBS script
- [x] Create FB test directory and PBS script
- [ ] Run tests on HPC
- [ ] Evaluate results and document in `ALTERNATIVE_METHODS_COMPARISON.md`

---

## Priority 3: Investigate Energy-Based Rydberg Detection

### Concept
Instead of using `nRydberg = nBasis - nMINAO` (which fails for heavy elements), use an energy cutoff:
- **Rydberg orbitals**: Virtual orbitals with ε > threshold (e.g., 0.5 Ha or 1.0 Ha)
- **Valence virtuals**: Virtual orbitals with ε < threshold

### Implementation Options
1. Modify Serenity to add energy-based Rydberg option for IBO
2. Pre-process orbitals to reorder by energy before IBO
3. Use `settings.useEnergyCutOff = true` with appropriate `virtualEnergyCutOff`

### Research Needed
- [ ] Check if Serenity already supports energy-based virtual classification
- [ ] Determine appropriate energy threshold for heavy elements
- [ ] Test on Po₂ and compare with MINAO-based approach

---

## Priority 4: Investigate Alternative MINAO Definitions

### Problem
Po MINAO has only 13 functions (2s + 6p + 5d), which is too small relative to the ANO-RCC-VDZP basis (68 functions per atom).

### Potential Solutions
1. **Expand Po MINAO**: Add more shells (4f, 5s, 5p, etc.) to better represent occupied space
2. **Use different minimal basis**: ANO-S, STO-3G, or custom minimal basis
3. **Scale MINAO count**: Artificially inflate nMINAO for heavy elements

### Location
`serenity/data/basis/MINAO` - Po entry starts at line ~XXXX

---

## Priority 5: SO-CASSI Workflow (After Localization Works)

Once a localization method works for Po₂, proceed to the full workflow:

### Target
- **System**: Po₂ (or other heavy element dimer)
- **Method**: SO-CASSI (Spin-Orbit Complete Active Space State Interaction)
- **Structures**: 5-10 geometries spanning the potential energy curve

### Workflow
1. Generate geometries (equilibrium + stretched/compressed)
2. Run OpenMolcas DKH2 SCF for each geometry
3. Run autoCAS consistent active space protocol
4. Extract common active space across all geometries
5. Run SO-CASSI calculations in OpenMolcas

### Structure Generation
```
Po-Po distances (Å): 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 6.0, 8.0, 10.0
```

---

## File Checklist

### Created
- [x] `tests/autocas/localization_methods/Po2_PM/` - PM test
- [x] `tests/autocas/localization_methods/Po2_FB/` - FB test
- [x] `tests/autocas/localization_methods/README.md` - Test documentation
- [x] `autocas/.../configuration.py` - Added `localization_method` attribute
- [x] `autocas/.../protocol.py` - Added `-L` CLI option

### To Create
- [ ] `research/localization/ALTERNATIVE_METHODS_COMPARISON.md` - Results after running tests

### To Modify (if needed)
- [ ] `serenity/data/basis/MINAO` - Potentially expand Po entry (if PM/FB also fail)

---

## References

- [IBO_RYDBERG_OVERFLOW_FIX.md](../research/localization/IBO_RYDBERG_OVERFLOW_FIX.md) - Analysis of the overflow issue
- [IBO_ENERGY_CUTOFF_ANALYSIS.md](../research/localization/IBO_ENERGY_CUTOFF_ANALYSIS.md) - Energy cutoff research
- [HPC_BUILD_HORTENSE.md](HPC_BUILD_HORTENSE.md) - Build instructions