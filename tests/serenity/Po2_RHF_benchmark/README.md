# Serenity Po2 RHF Benchmark

Benchmark test to measure Serenity RHF calculation time for Po2 with ANO-RCC-VDZP basis set.

## Purpose

Compare RHF timing between Serenity and OpenMolcas for heavy elements.

## Files

- `Po2.xyz` - Po2 geometry (2.0 Angstrom bond length)
- `Po2_RHF.input` - Serenity input file
- `job_serenity_rhf.pbs` - PBS job script (edit PROJECT variable)

## Running on HPC

```bash
# Edit the PROJECT variable in job script
nano job_serenity_rhf.pbs

# Submit job
qsub job_serenity_rhf.pbs
```

## Expected Output

- SCF energy
- Timing information (wall time)
