# Po2 Overlap Diagnostics Tests

Tests to capture Serenity's overlap matrix eigenvalue diagnostics for linear dependency investigation.

## Purpose

These tests run autoCAS with the new Serenity diagnostics (commit `f117000`) to collect eigenvalue spectra for:
- **S1**: AO overlap matrix
- **S2**: MINAO overlap matrix
- **EQ1**: IAO orthogonalization matrix
- **EQ2**: othoA orthogonalization matrix

## Test Structure

```
Po2_overlap_diagnostics/
├── README.md
├── VDZP/
│   ├── submit_all.sh      # Master script - just run this!
│   ├── scf_single.pbs     # Single geometry SCF (submitted in parallel)
│   ├── run_10geom.pbs     # autoCAS job (auto-waits for SCF)
│   └── po2_*.xyz          # 10 geometry files
├── VTZP/
│   └── (same structure)
└── VQZP/
    └── (same structure)
```

## Running the Tests

**Just run `submit_all.sh`** - it handles everything:

```bash
# On HPC (Hortense)
cd /path/to/Po2_overlap_diagnostics/VDZP
./submit_all.sh
```

This will:
1. Submit 10 SCF jobs **in parallel** (one per geometry)
2. Submit the autoCAS job with `depend=afterok` on all SCF jobs
3. autoCAS automatically starts when all SCF jobs complete

Repeat for VTZP and VQZP directories.

## Geometries

10 geometries selected from the 25-point dissociation curve:

| Index | Distance (Å) | Description |
|-------|-------------|-------------|
| 000   | 2.10        | Near equilibrium |
| 003   | 2.40        | |
| 005   | 2.60        | |
| 007   | 2.80        | |
| 009   | 3.00        | |
| 011   | 3.50        | |
| 013   | 4.00        | |
| 015   | 4.50        | |
| 017   | 5.00        | |
| 019   | 6.00        | Stretched |

## Resource Allocation

| Basis | SCF Jobs | SCF Memory | autoCAS Memory |
|-------|----------|------------|----------------|
| VDZP  | 4 cores, 1h | 16 GB | 64 GB |
| VTZP  | 4 cores, 1.5h | 24 GB | 64 GB |
| VQZP  | 4 cores, 2h | 32 GB | 84 GB |

## Expected Output

The diagnostics will appear in `autocas_output.log`:

```
=== AO Overlap Matrix (S1) Diagnostics ===
  Basis functions:    136
  Min eigenvalue:     X.XXXe-XX
  Max eigenvalue:     X.XXX
  Condition number:   X.XXXe+XX
  Eigenvalues < 1e-6:  N
  Eigenvalues < 1e-8:  N
  Eigenvalues < 1e-10: N
```

## Monitoring

```bash
# Check job status
qstat -u $USER

# View running/queued jobs
qstat -u $USER | grep -E "po2_scf|po2_diag"
```

## Analysis

Compare eigenvalue spectra across basis sets to identify:
1. Which matrices show near-singularity (eigenvalues < 1e-6)
2. How condition numbers scale with basis set size
3. Correlation between eigenvalue spectra and CASSCF convergence failures
