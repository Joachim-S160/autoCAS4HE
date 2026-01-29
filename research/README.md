# autoCAS4HE Research Documentation

Research notes and analysis for extending autoCAS to heavy elements.

**End goal**: Create dissociation profiles using SO-CASSI / SO-MPSSI in OpenMolcas for Po-containing molecules (Po2, Po(OH)4, PoPb, PoBi, etc.) with consistent active spaces selected by autoCAS.

---

## Directory Structure

```
research/
├── README.md                                   # This file
├── PO2_AUTOCAS_ERROR_ANALYSIS.md                # Po2 IBO crash analysis (first crash)
├── localization/                                # IBO/IAO localization for heavy elements
│   ├── IBO_MINAO_FIX_PLAN_290126.md             # ★ Main fix plan: MINAO expansion + code fixes
│   ├── AUTOCAS_EXPANDED_MINAO_COMPATIBILITY.md  # ★ autoCAS compatibility analysis
│   ├── IBO_MINAO_BASIS_TOO_SMALL.md             # Bug report: second crash (MINAO < nOcc)
│   ├── IBO_RYDBERG_OVERFLOW_FIX.md              # Rydberg overflow fix (energy cutoff)
│   ├── IBO_ENERGY_CUTOFF_ANALYSIS.md            # Energy cutoff mechanism details
│   ├── IBO_VS_OTHER_LOCALIZATION.md             # Why IBO over PM/Foster-Boys
│   ├── VIRTUAL_ORBITAL_LOCALIZATION_ANALYSIS.md # Virtual orbital localization details
│   └── LOCALIZATION_STABILITY_TESTING.md        # Future stability test plan
└── relativistic/                                # Relativistic treatment
    ├── SERENITY_RELATIVISTIC_SUPPORT.md          # Serenity capabilities (none)
    └── OPENMOLCAS_ORBITAL_INTEGRATION.md         # OpenMolcas DKH2 orbital workflow
```

---

## Key Documents

### Active Fix Plan

| Document | Summary |
|----------|---------|
| [IBO_MINAO_FIX_PLAN_290126.md](localization/IBO_MINAO_FIX_PLAN_290126.md) | **Main plan**: Expand MINAO from valence-only to all-shells (ANO-RCC) for Z >= 39, fix IBOLocalization.cpp check, guard IAOPopulationCalculator against nOcc >= nMINAO, remap orbitalRange. |
| [AUTOCAS_EXPANDED_MINAO_COMPATIBILITY.md](localization/AUTOCAS_EXPANDED_MINAO_COMPATIBILITY.md) | **Compatibility analysis**: Verifies expanded MINAO is safe for autoCAS (CAS size, DMRG cost, DOS orbital mapping, plateau detection, larger molecules). Includes ROSE assessment and OpenMolcas orbital transfer. |

### Bug Reports and Fixes (chronological)

| Document | Summary |
|----------|---------|
| [PO2_AUTOCAS_ERROR_ANALYSIS.md](PO2_AUTOCAS_ERROR_ANALYSIS.md) | **Crash 1**: Core orbital assigned as virtual due to non-relativistic orbital energy misordering. Fixed by energy-based Rydberg cutoff. |
| [IBO_RYDBERG_OVERFLOW_FIX.md](localization/IBO_RYDBERG_OVERFLOW_FIX.md) | Rydberg overflow fix using energy cutoff at 1.0 Ha. |
| [IBO_MINAO_BASIS_TOO_SMALL.md](localization/IBO_MINAO_BASIS_TOO_SMALL.md) | **Crash 2**: MINAO basis too small (26 < 84 occupied). Exposed after crash 1 was fixed. |

### Background Research

| Document | Summary |
|----------|---------|
| [IBO_ENERGY_CUTOFF_ANALYSIS.md](localization/IBO_ENERGY_CUTOFF_ANALYSIS.md) | How Serenity's -5 Ha energy cutoff classifies core orbitals. Fails for Z > 50 without relativistic treatment. |
| [IBO_VS_OTHER_LOCALIZATION.md](localization/IBO_VS_OTHER_LOCALIZATION.md) | Why IBO is preferred: basis-independent, physically meaningful, needed for DOS orbital mapping. |
| [VIRTUAL_ORBITAL_LOCALIZATION_ANALYSIS.md](localization/VIRTUAL_ORBITAL_LOCALIZATION_ANALYSIS.md) | Virtual orbital localization and reconstruction details. |
| [SERENITY_RELATIVISTIC_SUPPORT.md](relativistic/SERENITY_RELATIVISTIC_SUPPORT.md) | Serenity has **no** scalar relativistic support (DKH, X2C, ZORA). |
| [OPENMOLCAS_ORBITAL_INTEGRATION.md](relativistic/OPENMOLCAS_ORBITAL_INTEGRATION.md) | OpenMolcas DKH2 → Serenity IBO pipeline. |

---

## Pipeline Overview

```
OpenMolcas (DKH2 SCF)
    → Serenity (IBO localization with expanded MINAO)
        → autoCAS (DOS orbital mapping + S1 plateau detection)
            → OpenMolcas (CASSCF/DMRGSCF with autoCAS-selected CAS)
                → OpenMolcas (SO-CASSI / SO-MPSSI)
                    → Dissociation profiles with spin-orbit coupling
```

---

## Current Status

| Component | Status |
|-----------|--------|
| OpenMolcas DKH2 SCF | Working |
| Serenity IBO (light elements) | Working |
| Serenity IBO (heavy elements) | **Blocked** — MINAO fix needed |
| autoCAS CAS selection | Working (tested on light elements) |
| MINAO expansion plan | **Ready** — IBO_MINAO_FIX_PLAN_290126.md |
| Compatibility analysis | **Done** — safe for all target molecules |
| SO-CASSI/SO-MPSSI | Not yet started (depends on MINAO fix) |

---

## Future Investigations

1. **ROSE software** (Senjean et al.): Alternative to Serenity for IAO/IBO, handles heavy elements natively. Most viable via PySCF scalar-X2C. See AUTOCAS_EXPANDED_MINAO_COMPATIBILITY.md Section 10.
2. **Expanded chemical valence**: Include 5d in Po/Bi valence definition for larger initial CAS. See Section 8.
3. **OpenMolcas → PySCF switch**: If ROSE is adopted, orbital transfer via MOKIT. See Section 12.
