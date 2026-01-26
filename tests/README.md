# autoCAS4HE Tests

Benchmark tests and test outputs for heavy element calculations.

---

## Directory Structure

```
tests/
├── README.md                         # This file
├── RHF_BENCHMARK_COMPARISON.md       # Serenity vs OpenMolcas benchmark results
├── serenity/
│   └── Po2_RHF_benchmark/            # Serenity RHF test (non-relativistic)
├── molcas/
│   └── Po2_RHF_benchmark/            # OpenMolcas RHF test (DKH2)
└── autocas/
    ├── serenity_scf/                 # Tests using Serenity for SCF (standard workflow)
    │   ├── N2_test/                  # N2 test with Serenity SCF
    │   ├── N2_ANO_test/              # N2 with ANO basis
    │   └── Po2_test/                 # Po2 test (crashed due to IBO issue)
    └── external_scf/                 # Tests using external orbitals (new workflow)
        └── N2_test/                  # N2 test with OpenMolcas SCF orbitals
```

---

## autoCAS Workflow Types

### Standard Workflow (`serenity_scf/`)

Uses Serenity for the entire orbital preparation:
1. Serenity runs SCF (non-relativistic)
2. Serenity performs IBO localization
3. Serenity does DOS orbital mapping
4. OpenMolcas runs DMRG-CI for entropy calculation

**Limitation**: No relativistic effects → fails for heavy elements (Z > 50)

### External Orbital Workflow (`external_scf/`)

Uses external program (e.g., OpenMolcas with DKH2) for SCF:
1. **OpenMolcas** runs SCF with DKH2 scalar relativistic Hamiltonian
2. autoCAS loads external orbitals into Serenity (skips Serenity SCF)
3. Serenity performs IBO localization
4. Serenity does DOS orbital mapping
5. OpenMolcas runs DMRG-CI for entropy calculation

**Usage**:
```bash
scine_autocas_consistent_active_space -e -o orbital_0.ScfOrb,orbital_1.ScfOrb system_0.xyz system_1.xyz
```

Or via YAML:
```yaml
use_external_orbitals: true
external_orbital_files:
  - /path/to/system_0.ScfOrb
  - /path/to/system_1.ScfOrb
```

**Advantage**: Correct relativistic treatment for heavy elements

---

## Benchmark Results

| Document | Description |
|----------|-------------|
| [RHF_BENCHMARK_COMPARISON.md](RHF_BENCHMARK_COMPARISON.md) | Po2 RHF timing and energy comparison. OpenMolcas is 128x faster; ~9640 Hartree energy difference due to relativistic effects. |

---

## Key Findings

- **OpenMolcas**: 2.25 min, E = -44341.68 Ha (DKH2)
- **Serenity**: 288 min, E = -34701.36 Ha (non-relativistic)
- **Po2 autoCAS crashed** during IBO localization (standard workflow)
- **Solution**: Use external orbital workflow with DKH2 orbitals

---

## Related Documentation

For research notes and analysis, see [../research/README.md](../research/README.md):
- Error analysis: [research/PO2_AUTOCAS_ERROR_ANALYSIS.md](../research/PO2_AUTOCAS_ERROR_ANALYSIS.md)
- Localization methods: [research/localization/](../research/localization/)
- Relativistic treatment: [research/relativistic/](../research/relativistic/)
