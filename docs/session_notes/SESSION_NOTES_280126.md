# Session Notes - 28/01/2026

## Objective
Fix IBO core/valence classification visualization and create systematic dimer test suite for studying IBO energy cutoffs across the PSE.

## Completed Tasks

### 1. IBO_distr.py Visualization Improvements
- **Colors**: Changed to colorblind-friendly palette (dark red, blue, purple, orange)
- **Bar visibility**: Added black edge colors, consistent bin widths via common `bin_edges`
- **Background regions**: Light hues showing core/valence/Rydberg zones
- **Legend**: Shows orbital counts per category
- **Title**: Includes MINAO count (total and per-atom)

### 2. Serenity IBO Classification Verification
Critically assessed script accuracy against Serenity source code:

| File | Key Logic |
|------|-----------|
| `OrbitalController.cpp:713-728` | Core: `eigenvalue < -5.0 Ha` → flag=1 |
| `OrbitalController.cpp:675-699` | Rydberg: top N by energy → flag=2, crashes if flag=1 |
| `LocalizationTask.cpp:152-173` | `nRydberg = nBasis - nMINAO` |

**Critical finding**: Serenity throws error if core orbital selected as Rydberg. Script now detects and reports this.

### 3. Overflow Detection Added
Script now reports Serenity crash conditions:
```
N2:  STATUS: IBO should work
Po2: STATUS: IBO WILL CRASH - nRydberg > nVirtual
     !! OVERFLOW: 58 orbitals into occupied space
     !! Core-Rydberg overlap: 36 (would crash Serenity)
```

### 4. PSE Dimer Test Suite Created
- **Location**: `tests/IBO_dimer_study/`
- **Elements**: 61 dimers (H-Po, excluding noble gases)
- **Contents per element**:
  - `{el}2_0.xyz` / `{el}2_1.xyz` (equilibrium / stretched)
  - `{el}2_0_scf.input` / `{el}2_1_scf.input` (OpenMolcas DKH2)
  - `{el}2_dkh2.pbs` (job script)
- **Master scripts**: `submit_all.sh`, `analyze_all.sh`

### 5. Supporting Scripts
- `scripts/dimer_data.py` - Bond lengths, spin multiplicities for all elements
- `scripts/generate_dimer_tests.sh` - Generator for test directories

## Key Files Modified
- `scripts/IBO_distr.py` - Complete rewrite of classification and visualization

## Git Status
Committed: `8ac81ce` - IBO analysis scripts and dimer test suite
Local changes: Updated IBO_distr.py with Serenity-accurate classification (not yet pushed)

## Next Steps
1. Push updated IBO_distr.py
2. Submit dimer calculations on cluster
3. Analyze results to determine element-dependent energy cutoffs
4. Investigate MINAO expansion for heavy elements
