# Po2 SO-CASSI Test

SO-CASSI workflow for Po2 using autoCAS-derived active space CAS(12,8).

## Workflow

```
autoCAS singlet orbitals (system_X.RasOrb)
    |
    v
Singlet RASSCF + MS-CASPT2 --> JobMix.S1
    | (use singlet orbitals)
    v
Triplet RASSCF + MS-CASPT2 --> JobMix.S3
    | (use triplet orbitals)
    v
Quintet RASSCF + MS-CASPT2 --> JobMix.S5
    |
    v
SO-CASSI (RASSI with SPINORBIT, EJOB, OMEGA)
```

## Files

- `Po2_equilibrium.xyz` - Equilibrium geometry (R = 2.3 A)
- `Po2_dissociated.xyz` - Dissociated geometry (R = 5.0 A)
- `Po2_so_cassi.input` - OpenMolcas input (update FILEORB path before running)
- `job_so_cassi.pbs` - PBS job script

## Before Running

1. Run autoCAS `consistent_active_space` for singlet Po2
2. Update `FILEORB` in `Po2_so_cassi.input` to point to your `final/system_X.RasOrb`
3. Submit: `qsub job_so_cassi.pbs`

## Active Space

- CAS(12,8): 12 electrons in 8 orbitals
- 80 inactive orbitals
- ANO-RCC-VQZP basis set

## Root Counts

- Singlet: 28 roots
- Triplet: 90 roots
- Quintet: 50 roots

## Expected Output

- `JobMix.S1`, `JobMix.S3`, `JobMix.S5` - CASPT2 JOBIPH files
- `Singlet.RasOrb`, `Triplet.RasOrb` - Optimized orbital files
- SO-CASSI energies in RASSI output

## Verification

- Compare ground state to experimental dissociation energy: ~1.90 eV
- Check Omega values for linear molecule (0+, 0-, 1, 2, etc.)
