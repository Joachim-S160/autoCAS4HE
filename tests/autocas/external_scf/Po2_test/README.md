# Po2 External Orbital Test (DKH2)

This test validates the external orbital workflow for **heavy elements** where relativistic effects are essential.

## Purpose

Test the workflow where:
1. OpenMolcas generates SCF orbitals **with DKH2** (Douglas-Kroll-Hess 2nd order)
2. autoCAS loads these relativistic orbitals into Serenity (skipping Serenity SCF)
3. Serenity performs IBO localization
4. autoCAS continues with entropy-based active space selection

## Why DKH2?

Polonium (Z=84) is a heavy element where relativistic effects significantly impact:
- Core orbital energies (contracted by ~9600 Hartree vs non-relativistic)
- Valence orbital shapes and energies
- IBO localization stability (non-relativistic orbitals cause crashes)

The DKH2 Hamiltonian (`Relativistic = R02O` in SEWARD) provides scalar relativistic corrections that are essential for meaningful results.

## Test Setup

- **Molecule**: Po2 (polonium dimer)
- **Geometries**:
  - `po2_0.xyz`: 2.0 Å bond length
  - `po2_1.xyz`: 4.0 Å bond length (stretched)
- **Basis**: ANO-RCC-VDZP (relativistic contracted basis)
- **Relativistic**: DKH2 (R02O)

## Running on HPC

```bash
qsub po2_external.pbs
```

## Expected Outcome

- OpenMolcas generates `.ScfOrb` files with DKH2 orbitals (~-44341 Ha energy)
- autoCAS loads these orbitals (prints "Loading external orbitals...")
- IBO localization runs **without crashing** (unlike non-relativistic)
- Active space selection completes
- Final DMRGSCF calculation produces meaningful energies

## Comparison

| Workflow | SCF Method | Energy (Ha) | IBO Status |
|----------|------------|-------------|------------|
| Serenity SCF | Non-relativistic | ~-34701 | **Crashes** |
| External DKH2 | DKH2 relativistic | ~-44341 | Works |

The ~9640 Hartree difference is due to relativistic contraction of core orbitals.
