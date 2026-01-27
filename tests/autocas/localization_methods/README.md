# Localization Methods Tests

This directory contains tests for alternative orbital localization methods for Po2.

## Background

IBO (Intrinsic Bond Orbitals) localization fails for Po2 because:
- MINAO basis for Po is too small (13 functions per atom)
- This causes Rydberg orbital overflow into occupied space
- See [IBO_RYDBERG_OVERFLOW_FIX.md](../../../research/localization/IBO_RYDBERG_OVERFLOW_FIX.md)

## Alternative Localization Methods

| Method | Flag | Description | MINAO Required? | Virtual Localization? |
|--------|------|-------------|-----------------|----------------------|
| IBO | `-L IBO` | Intrinsic Bond Orbitals (default) | Yes - fails for Po2 | Yes |
| Pipek-Mezey | `-L PIPEK_MEZEY` | Mulliken population localization | No | No (auto-disabled) |
| Foster-Boys | `-L BOYS` | Spatial extent minimization | No | No (auto-disabled) |
| Edmiston-Ruedenberg | `-L EDMINSTON_RUEDENBERG` | Coulomb self-repulsion maximization | No | No (auto-disabled) |

**Note**: Virtual orbital localization is only implemented for IBO/IAO in Serenity. When using PM, FB, or ER, the code automatically disables virtual localization. This means only occupied orbitals will be localized.

## Test Directories

### Po2_PM/
Tests Pipek-Mezey localization for Po2 with external DKH2 orbitals.

```bash
cd Po2_PM
qsub po2_pm.pbs
```

### Po2_FB/
Tests Foster-Boys localization for Po2 with external DKH2 orbitals.

```bash
cd Po2_FB
qsub po2_fb.pbs
```

## How to Run

1. Ensure the HPC environment is set up (see [HPC_BUILD_HORTENSE.md](../../../docs/HPC_BUILD_HORTENSE.md))
2. Submit the PBS jobs:
   ```bash
   cd Po2_PM && qsub po2_pm.pbs
   cd ../Po2_FB && qsub po2_fb.pbs
   ```

## Prerequisites

The tests require pre-computed DKH2 orbitals (`.scf.h5` files) from OpenMolcas. These are already included in the test directories, copied from the external_scf/Po2_test.

## Expected Outcomes

### Success
- Localization completes without crash
- Active space selection proceeds
- DMRGSCF calculation runs

### Failure Modes
- If both PM and FB fail, there may be a deeper incompatibility with Serenity for heavy elements
- Check error logs for details

## CLI Option Added

The `-L/--localization` option was added to `scine_autocas_consistent_active_space`:

```bash
scine_autocas_consistent_active_space -e -o "orb1.h5,orb2.h5" -L PIPEK_MEZEY -b ANO-RCC-VDZP mol1.xyz mol2.xyz
```

Options:
- `IBO` (default)
- `PIPEK_MEZEY`
- `BOYS`
- `EDMINSTON_RUEDENBERG`

## Files Changed

- `autocas/scine_autocas/workflows/consistent_active_space/configuration.py` - Added `localization_method` attribute
- `autocas/scine_autocas/workflows/consistent_active_space/protocol.py` - Added `-L` CLI option
