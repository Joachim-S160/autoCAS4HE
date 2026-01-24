# autoCAS4HE Research Documentation

Research notes and analysis for extending autoCAS to heavy elements.

---

## Directory Structure

```
research/
├── README.md                          # This file
├── PO2_AUTOCAS_ERROR_ANALYSIS.md      # Po2 IBO crash analysis
├── localization/                      # Orbital localization methods
│   ├── IBO_ENERGY_CUTOFF_ANALYSIS.md  # Energy cutoff mechanism and failures
│   ├── IBO_VS_OTHER_LOCALIZATION.md   # Why IBO over PM/Foster-Boys
│   └── LOCALIZATION_STABILITY_TESTING.md  # Future stability test plan
└── relativistic/                      # Relativistic treatment
    ├── SERENITY_RELATIVISTIC_SUPPORT.md   # Serenity capabilities (none)
    └── OPENMOLCAS_ORBITAL_INTEGRATION.md  # Proposed DKH2 orbital workflow
```

---

## Key Documents

### Error Analysis

| Document | Summary |
|----------|---------|
| [PO2_AUTOCAS_ERROR_ANALYSIS.md](PO2_AUTOCAS_ERROR_ANALYSIS.md) | Why Po2 autoCAS crashes during IBO localization. Root cause: non-relativistic orbital energies cause core-valence misclassification. |

### Localization

| Document | Summary |
|----------|---------|
| [localization/IBO_ENERGY_CUTOFF_ANALYSIS.md](localization/IBO_ENERGY_CUTOFF_ANALYSIS.md) | How the -5.0 Hartree energy cutoff determines core orbitals, and why it fails for Z > 50 without relativistic treatment. |
| [localization/IBO_VS_OTHER_LOCALIZATION.md](localization/IBO_VS_OTHER_LOCALIZATION.md) | Why IBO is preferred over Pipek-Mezey and Foster-Boys for physically meaningful orbitals. |
| [localization/LOCALIZATION_STABILITY_TESTING.md](localization/LOCALIZATION_STABILITY_TESTING.md) | Test plan for validating orbital stability under geometry distortions. |

### Relativistic Treatment

| Document | Summary |
|----------|---------|
| [relativistic/SERENITY_RELATIVISTIC_SUPPORT.md](relativistic/SERENITY_RELATIVISTIC_SUPPORT.md) | Investigation confirms Serenity has **no** scalar relativistic support (DKH, X2C, ZORA). |
| [relativistic/OPENMOLCAS_ORBITAL_INTEGRATION.md](relativistic/OPENMOLCAS_ORBITAL_INTEGRATION.md) | Proposed workflow: Use OpenMolcas DKH2 for SCF, import orbitals to Serenity for IBO localization. |

---

## Main Findings

1. **Serenity lacks relativistic support** - No DKH, X2C, or ZORA
2. **IBO is the right method** - But needs correct input orbital energies
3. **Solution**: OpenMolcas DKH2 → Serenity IBO pipeline
4. **Serenity already supports** reading MOLCAS orbital files

---

## TODO

- [ ] Research relativistic localization methods in literature
- [ ] Implement OpenMolcas → Serenity orbital workflow
- [ ] Run stability tests for IBO under geometry distortions
- [ ] Consider long-term: contribute scalar relativistic support to Serenity
