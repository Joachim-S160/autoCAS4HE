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

### Available Localization Methods
| Method | Flag | Description | Basis Dependent? |
|--------|------|-------------|------------------|
| IBO | `IBO` | Intrinsic Bond Orbitals | Yes (MINAO) |
| Pipek-Mezey | `PM` | Mulliken population localization | More basis-dependent |
| Foster-Boys | `FB` | Spatial extent minimization | No |
| Edmiston-Ruedenberg | `ER` | Coulomb self-repulsion maximization | No |

### Test Plan
Create test folders under `tests/autocas/localization_methods/`:
```
tests/autocas/localization_methods/
├── Po2_PM/          # Pipek-Mezey
├── Po2_FB/          # Foster-Boys
├── Po2_ER/          # Edmiston-Ruedenberg (if available)
└── README.md
```

Each test should:
1. Use external OpenMolcas DKH2 orbitals (`.scf.h5`)
2. Specify the localization method via autoCAS settings
3. Check if localization completes without crash
4. Evaluate quality of resulting orbitals

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

### To Create
- [ ] `tests/autocas/localization_methods/Po2_PM/` - PM test
- [ ] `tests/autocas/localization_methods/Po2_FB/` - FB test
- [ ] `tests/autocas/localization_methods/README.md` - Test documentation
- [ ] `research/localization/ALTERNATIVE_METHODS_COMPARISON.md` - Results

### To Modify
- [ ] `serenity/src/tasks/LocalizationTask.cpp` - Revert on main branch
- [ ] `serenity/data/basis/MINAO` - Potentially expand Po entry

---

## References

- [IBO_RYDBERG_OVERFLOW_FIX.md](../research/localization/IBO_RYDBERG_OVERFLOW_FIX.md) - Analysis of the overflow issue
- [IBO_ENERGY_CUTOFF_ANALYSIS.md](../research/localization/IBO_ENERGY_CUTOFF_ANALYSIS.md) - Energy cutoff research
- [HPC_BUILD_HORTENSE.md](HPC_BUILD_HORTENSE.md) - Build instructions