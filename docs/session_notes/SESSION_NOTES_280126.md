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
- **Dual-panel layout**: Core region on LEFT, valence/Rydberg on RIGHT
- **Right panel starts at -6 Ha**: Red hue preserved for E < -5 Ha even without core orbitals
- **"SERENITY FAILS" warning**: Prominent red text on plots when IBO will crash

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

### 6. Animation Scripts (GIF + MP4)
- **Script**: `scripts/create_IBO_gif.py`
- **Features**:
  - Creates both GIF and MP4 from IBO distribution PNGs
  - Sorted by atomic number (chemical size), not alphabetically
  - MP4 easier to pause in VSCode than GIF
  - Shows summary of failing elements at the end
- **Output**: `IBO_all_elements.gif`, `IBO_all_elements.mp4`

### 7. Dimer Study Results - Full PSE Analysis
Ran analysis on all 61 dimers. Results in `tests/IBO_dimer_study/IBO_diagnostics.csv`:

| Category | Count | Description |
|----------|-------|-------------|
| **IBO OK** | 18 (30%) | H, Be, C, N, F, Li, Na, Mg, K, Ca, P, Cl, As, Br, Cr, Mn, Cu, Zn |
| **SCF Convergence Issues** | 32 (52%) | Positive HOMO (unbound electrons) - O, S, Si, B, Al, Ga, Ge, Se, etc. |
| **Rydberg Overflow** | 11 (18%) | AG, AT, AU, BI, CD, HG, I, MO, PO, SB, W |

### 8. Rydberg Cutoff Analysis - E >= 1.0 Ha Criterion
**Question**: Would changing from `nRydberg = nBasis - nMINAO` to `Rydberg = orbitals with E >= 1.0 Ha` fix the issues?

**Answer**: **PARTIAL FIX ONLY**

| Scenario | Count | Result |
|----------|-------|--------|
| Already working | 18 | No change needed |
| SCF convergence issues | 32 | **Cannot be fixed by ANY Rydberg criterion** - need different basis/spin |
| Rydberg overflow | 11 | **WOULD be fixed** - all orbitals with E >= 1.0 Ha are virtual |

**Key insight**: 32 elements have positive HOMO energies (e.g., O₂ HOMO = +3.37 Ha), indicating unbound electrons. This is an SCF issue, not a Rydberg classification problem. These dimers may need:
- Different spin multiplicities
- Smaller basis sets
- Fractional occupation or multi-reference treatment

**Helper script**: `scripts/analyze_rydberg_cutoff.py` - run on HPC for exact orbital counts.

## Key Files Modified
- `scripts/IBO_distr.py` - Complete rewrite of classification and visualization
- `scripts/create_IBO_gif.py` - New animation generator
- `scripts/analyze_rydberg_cutoff.py` - New Rydberg cutoff analysis tool
- `tests/IBO_dimer_study/analyze_all.sh` - Updated with animation generation

## Git Status
- Commit `18a9b4b`: Added IBO_diagnostics.csv with full PSE analysis results
- All changes pushed to remote

## Next Steps
1. ~~Push updated IBO_distr.py~~ ✓
2. ~~Submit dimer calculations on cluster~~ ✓
3. ~~Analyze results to determine element-dependent energy cutoffs~~ ✓
4. Investigate SCF convergence for 32 failing elements (unbound electrons)
5. Consider element-specific spin multiplicities (e.g., O₂ triplet)
6. Test E >= 1.0 Ha Rydberg criterion in Serenity fork
7. Investigate MINAO expansion for heavy elements
