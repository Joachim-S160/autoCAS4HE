# Session Notes - 2026-01-24

## Summary of Work Completed

### 1. Po2 RHF Benchmark Tests

Created and ran benchmark tests comparing Serenity vs OpenMolcas for Po2 RHF with ANO-RCC-VDZP:

| Code | Time | Energy (Hartree) | Relativistic |
|------|------|------------------|--------------|
| OpenMolcas | 2.25 min | -44341.68 | DKH2 |
| Serenity | 288 min (4.8 hrs) | -34701.36 | Non-relativistic |

**Key findings:**
- OpenMolcas is ~128x faster
- Energy difference of ~9640 Hartree due to scalar relativistic effects
- Serenity has no DKH/X2C support

### 2. Po2 autoCAS Error Analysis

The Po2 autoCAS job crashed during IBO localization with:
```
RuntimeError: A core orbital is assigned to be virtual. Something is wrong here!
```

**Root cause:** IBO localization assigns core/virtual orbitals by energy ordering. With non-relativistic treatment of Po (Z=84), the orbital energies are wrong, causing the algorithm to misclassify orbitals.

**Code locations:**
- Error thrown: `serenity/src/data/OrbitalController.cpp:694`
- Core assignment: `serenity/src/data/OrbitalController.cpp:640-665`
- Localization flow: `serenity/src/tasks/LocalizationTask.cpp:111-135`

### 3. Documentation

Created `tests/RHF_BENCHMARK_COMPARISON.md` with:
- Timing comparison
- Energy comparison
- Error analysis
- Code references
- Potential workarounds

### 4. Scripts and Tools

- Created `scripts/treesummary.sh` for test output analysis
- Updated `.gitignore` for test outputs

## Files Modified/Created

| File | Action |
|------|--------|
| `tests/RHF_BENCHMARK_COMPARISON.md` | Created - benchmark results and error analysis |
| `tests/serenity/Po2_RHF_benchmark/` | Test directory with results |
| `tests/molcas/Po2_RHF_benchmark/` | Test directory with results |
| `tests/autocas/Po2_test/` | Po2 autoCAS test (crashed) |
| `scripts/treesummary.sh` | Created - output tree generator |
| `docs/SESSION_NOTES_230126.md` | Created earlier today |

## Key Technical Insights

### Why Serenity fails for heavy elements

1. **No scalar relativistic support** - Serenity uses non-relativistic HF
2. **Energy ordering assumption** - IBO assumes core orbitals have lowest energies
3. **Wrong for high-Z** - Without relativistic effects, orbital energies are ~10,000 Hartree wrong

### Potential workarounds identified

1. `skip_localization = True` in serenity interface (hardcoded False in configuration.py:208)
2. Different localization method (PIPEK_MEZEY, BOYS instead of IBO)
3. Use OpenMolcas orbitals via `-s` flag
4. ECPs instead of all-electron basis

## Open Questions

1. Would skipping localization still give meaningful results?
2. Can we add `skip_localization` as a YAML-configurable option?
3. Is IBO even appropriate for heavy elements with localized f-orbitals?
4. How to convert OpenMolcas orbitals to Serenity format for `-s` flag?

## Next Steps

1. Test with `skip_localization = True`
2. Investigate alternative localization methods
3. Research OpenMolcas → Serenity orbital conversion
4. Consider impact of non-relativistic treatment on entropy-based CAS selection
