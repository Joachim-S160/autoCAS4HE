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

#### Key Elements Status (H, C, N, O, Pb, Bi, Po)

| Element | Status | HOMO (Ha) | Issue | E>=1.0 Ha fix? |
|---------|--------|-----------|-------|----------------|
| **H** | ✓ OK | -0.60 | None | N/A |
| **C** | ✓ OK | -0.46 | None | N/A |
| **N** | ✓ OK | -0.61 | None | N/A |
| **O** | ✗ SCF | **+3.37** | Unbound electrons (wrong spin?) | No |
| **Pb** | ✗ SCF | **+3.88** | Unbound electrons (wrong spin?) | No |
| **Bi** | ✗ Overflow | -0.28 | nRydberg > nVirtual | **Yes** |
| **Po** | ✗ Overflow | -0.23 | nRydberg > nVirtual | **Yes** |

**Key insight**: 32 elements have positive HOMO energies, indicating unbound electrons. This is an SCF issue, not a Rydberg classification problem.

**Important constraint**: Any energy-based Rydberg cutoff **must be larger than HOMO**. If HOMO > cutoff, occupied orbitals would be classified as Rydberg (problematic for excited states).

#### SCF Failures - Full List (32 elements)

**Triplet ground states** (O, S, Se, Te - chalcogens):
| Element | HOMO (Ha) | Issue |
|---------|-----------|-------|
| O | +3.37 | Ground state is **³Σg⁻** (triplet), not singlet |
| S | +1.17 | Triplet ground state |
| Se | +0.92 | Triplet ground state |
| Te | +2.36 | Triplet ground state |

**Severe SCF failures** (5d/6d transition metals):
| Element | HOMO (Ha) | Issue |
|---------|-----------|-------|
| Os | +10.44 | Heavy 5d, needs multi-reference |
| Re | +10.27 | Heavy 5d, needs multi-reference |
| Ta | +9.04 | Heavy 5d, needs multi-reference |
| Hf | +8.28 | Heavy 5d, needs multi-reference |

**High-spin d-electrons** (3d transition metals):
| Element | HOMO (Ha) | Issue |
|---------|-----------|-------|
| Fe | +4.42 | High-spin d-electrons |
| Co | +4.38 | High-spin d-electrons |
| Ni | +5.10 | High-spin d-electrons |
| Ti | +3.04 | Open-shell d-electrons |
| V | +3.80 | Open-shell d-electrons |
| Sc | +2.70 | Open-shell d-electrons |

**Main group elements** (need different spin):
| Element | HOMO (Ha) | nVirt | Issue |
|---------|-----------|-------|-------|
| B | +2.42 | 0 | All orbitals occupied |
| Al | +1.56 | 0 | All orbitals occupied |
| Ga | +2.27 | 0 | All orbitals occupied |
| Ge | +2.26 | 0 | All orbitals occupied |
| Si | +0.84 | 0 | All orbitals occupied |
| In | +2.18 | 0 | All orbitals occupied |
| Sn | +2.17 | 0 | All orbitals occupied |
| Tl | +3.93 | 1 | Try different spin |
| Pb | +3.88 | 2 | Try different spin |

**4d/5d transition metals** (need multi-reference or different spin):
| Element | HOMO (Ha) | Issue |
|---------|-----------|-------|
| Y | +1.35 | Open-shell |
| Zr | +1.82 | Open-shell |
| Nb | +1.91 | Open-shell |
| Tc | +1.91 | Open-shell |
| Ru | +2.12 | Open-shell |
| Rh | +2.56 | Open-shell |
| Pd | +4.07 | Open-shell |
| Ir | +1.82 | Open-shell |
| Pt | +2.38 | Open-shell |

**Helper script**: `scripts/analyze_rydberg_cutoff.py` - run on HPC for exact orbital counts.

### 9. Bug Fixes
- Fixed `np.max(0, x)` → `max(0, x)` in IBO_distr.py (numpy syntax error)
- Skip plotting when HOMO > 0 (SCF failed) - results are unphysical
- Plot shows overlapping classifications (occupied + Rydberg bars for same orbital) to visualize where Serenity fails

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
