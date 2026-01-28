# Session Notes - 2026-01-27

## Summary of Work Completed

### 1. Added force_cas Option to Consistent CAS Workflow

Fixed the "SingleReferenceException" issue that occurred with FB localization by adding `-f/--force-cas` CLI option.

**Files modified:**
- `autocas/scine_autocas/workflows/consistent_active_space/configuration.py` - Added `force_cas` attribute
- `autocas/scine_autocas/workflows/consistent_active_space/protocol.py` - Added `-f` CLI option
- `autocas/scine_autocas/workflows/consistent_active_space/run_autocas.py` - Pass `force_cas` through workflow

### 2. Updated Localization Test Scripts

Added `-f` flag to both PM and FB test scripts:
- `tests/autocas/localization_methods/Po2_FB/po2_fb.pbs`
- `tests/autocas/localization_methods/Po2_PM/po2_pm.pbs`

## Investigation: DMRG Failure Root Cause

### Clarifications (NOT Issues)

1. **Spin = 0 in Serenity output**: This is the Ms value (spin projection), not multiplicity. S=0 means singlet, which is correct for closed-shell Po2.

2. **SPIN = 1 in Molcas input**: This is spin MULTIPLICITY (2S+1), so 1 = singlet. Correct.

3. **system_X_Y naming**: Serenity creates subsystems during localization with `splitValenceAndCore = True`:
   - system_0_0: 84 occ orbitals (full system)
   - system_0_1, _2, _3: 0 occ orbitals (core/valence/virtual partitions)

4. **Active space (12,8)**: 12 electrons in 8 orbitals - this is the valence CAS for Po2, correctly selected.

### ROOT CAUSE FOUND: NaN Orbital Coefficients

**Evidence (po2_fb.o13122491:748-851):**
```
Orbital                 1         2         3   ...
Energy             0.0000    0.0000    0.0000  ...
Occ. No.           0.0000    0.0000    0.0000  ...

1 PO1    1s            NaN       NaN       NaN  ...
2 PO1    2s            NaN       NaN       NaN  ...
```

**Confirmation (line 7389-7393):**
```
Warning! The number of occupied from the decomposition of the Inactive density
matrix is                      0  in symm.                      1
Expected value =                     78
Max diagonal of the density in symm.                      1  is equal to
                    NaN
```

**Error cascade:**
1. Serenity writes localized orbitals to system_1.scf.h5
2. Orbital coefficients are NaN (corrupted)
3. All orbital energies and occupations become 0
4. OpenMolcas density matrix has NaN values
5. DMRG integral transformation fails
6. QCMaquis throws `input stream error` (boost::archive::archive_exception)
7. DMRG crashes with return code -6

### Where Corruption Occurs

The NaN values appear during Serenity → Molcas orbital writing:
- `serenity.load_or_write_molcas_orbitals(True)` at protocol.py:147
- Uses `spy.OrbitalsIOTask_R(sys)` to write orbitals
- Something in the subsystem partitioning/recombination corrupts the coefficients

### Hypothesis

When `splitValenceAndCore = True` creates subsystems (system_0_0, system_0_1, etc.):
- The localized orbitals exist in these partitioned subsystems
- When writing back to Molcas, the original system may not have valid orbitals
- The `load_or_write_molcas_orbitals()` only iterates over `self.systems` (the 2 original systems)
- The partitioned subsystem orbitals are not being properly merged back

## Next Steps

1. **Debug Serenity orbital writing**: Add debug output to check orbital values before/after writing
2. **Check if issue is FB-specific**: Compare with PM test (same error suggests common code path)
3. **Test with skip_localization**: If this works, confirms localization/subsystem issue
4. **Consider workaround**: Load orbitals directly without Serenity localization for DMRG step

## Files and Code References

| Location | Description |
|----------|-------------|
| protocol.py:147 | Orbital writing call |
| serenity.py:232-254 | `load_or_write_molcas_orbitals()` |
| serenity.py:204 | `splitValenceAndCore = True` setting |
| po2_fb.o13122491:748 | First NaN values in output |
| po2_fb.o13122491:7389 | Warning about 0 occupied orbitals |
