# autoCAS4HE Tests

Benchmark tests and test outputs for heavy element calculations.

---

## Directory Structure

```
tests/
├── README.md                    # This file
├── RHF_BENCHMARK_COMPARISON.md  # Serenity vs OpenMolcas benchmark results
├── serenity/
│   └── Po2_RHF_benchmark/       # Serenity RHF test (non-relativistic)
├── molcas/
│   └── Po2_RHF_benchmark/       # OpenMolcas RHF test (DKH2)
└── autocas/
    └── Po2_test/                # Failed autoCAS run (IBO crash)
```

---

## Benchmark Results

| Document | Description |
|----------|-------------|
| [RHF_BENCHMARK_COMPARISON.md](RHF_BENCHMARK_COMPARISON.md) | Po2 RHF timing and energy comparison. OpenMolcas is 128x faster; ~9640 Hartree energy difference due to relativistic effects. |

---

## Key Findings

- **OpenMolcas**: 2.25 min, E = -44341.68 Ha (DKH2)
- **Serenity**: 288 min, E = -34701.36 Ha (non-relativistic)
- **Po2 autoCAS crashed** during IBO localization

---

## Related Documentation

For research notes and analysis, see [../research/README.md](../research/README.md):
- Error analysis: [research/PO2_AUTOCAS_ERROR_ANALYSIS.md](../research/PO2_AUTOCAS_ERROR_ANALYSIS.md)
- Localization methods: [research/localization/](../research/localization/)
- Relativistic treatment: [research/relativistic/](../research/relativistic/)
