# OpenMolcas Po2 RHF Benchmark

Benchmark test to measure OpenMolcas RHF calculation time for Po2 with ANO-RCC-VDZP basis set.

## Purpose

Compare RHF timing between Serenity and OpenMolcas for heavy elements.

## Files

- `Po2.xyz` - Po2 geometry (2.0 Angstrom bond length)
- `Po2_RHF.input` - OpenMolcas input file
- `job_molcas_rhf.pbs` - PBS job script (edit PROJECT variable)

## Running on HPC

```bash
# Edit the PROJECT variable in job script
nano job_molcas_rhf.pbs

# Submit job
qsub job_molcas_rhf.pbs
```

## Expected Output

- SCF energy
- Timing information from OpenMolcas log
