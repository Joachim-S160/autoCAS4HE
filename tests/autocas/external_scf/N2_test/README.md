# N2 External Orbital Test

This test validates the new `-e` (external orbitals) flag in autoCAS.

## Purpose

Test the workflow where:
1. OpenMolcas generates SCF orbitals (can use DKH2 for heavy elements)
2. autoCAS loads these orbitals into Serenity (skipping Serenity SCF)
3. Serenity performs IBO localization
4. autoCAS continues with entropy-based active space selection

## Test Setup

- **Molecule**: N2 (nitrogen dimer)
- **Geometries**:
  - `n2_0.xyz`: 1.1 Å (near equilibrium)
  - `n2_1.xyz`: 4.1 Å (stretched)
- **Basis**: ANO-S-MB (minimal basis for quick testing)

## Running the Test

```bash
./run_test.sh
```

This will:
1. Run OpenMolcas SCF for both geometries
2. Run `scine_autocas_consistent_active_space -e -o <orbital_files> <xyz_files>`

## Expected Outcome

- OpenMolcas generates `.ScfOrb` files for each geometry
- autoCAS loads these orbitals (prints "Loading external orbitals...")
- IBO localization runs without crashing
- Active space selection completes

## Comparison

Compare results with `../serenity_scf/N2_test/` which uses the standard workflow (Serenity SCF).
Results should be similar since N2 doesn't require relativistic treatment.
