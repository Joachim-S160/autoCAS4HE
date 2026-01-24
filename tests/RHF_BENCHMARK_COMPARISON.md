# Po2 RHF Benchmark Comparison: Serenity vs OpenMolcas

**Date:** 2026-01-24
**System:** Po2 at 2.0 Å bond length
**Basis:** ANO-RCC-VDZP (136 basis functions)
**HPC:** VSC Hortense, 16 cores, 32 GB RAM

---

## Timing Results

| Code | Wall Time | SCF Cycles |
|------|-----------|------------|
| **OpenMolcas** | **2.25 minutes** (134.91 s) | 5 |
| **Serenity** | **288 minutes** (4.8 hours) | 17 (Po2) + 12 (Po atom) |

**OpenMolcas is ~128x faster than Serenity for this calculation.**

---

## Energy Results

| Code | Total Energy (Hartree) | Relativistic Treatment |
|------|------------------------|------------------------|
| **OpenMolcas** | -44341.6825837401 | DKH2 (Douglas-Kroll-Hess order 2) |
| **Serenity** | -34701.3606231649 | Non-relativistic |

**Energy difference: ~9640 Hartree** - due to scalar relativistic effects!

---

## Key Observations

### 1. Relativistic Treatment
- **OpenMolcas** automatically uses DKH2 scalar relativistic Hamiltonian with ANO-RCC basis sets
- **Serenity** uses non-relativistic treatment by default
- For Polonium (Z=84), scalar relativistic effects are ~10,000 Hartree

### 2. Performance Difference
The 128x speed difference is likely due to:
- OpenMolcas uses Cholesky decomposition for 2-electron integrals
- Serenity uses conventional 4-center integrals without density fitting
- Heavy elements have many contracted basis functions, making integral evaluation expensive

### 3. Implications for autoCAS

**CRITICAL:** The Serenity SCF step in autoCAS will be extremely slow for heavy elements. Options:
1. Use OpenMolcas for initial orbitals (via `-s` flag with pre-computed orbitals)
2. Use ECPs instead of all-electron basis sets (too little bang for my buck)
3. Enable density fitting in Serenity (if available for HF, needs more research)
4. Given the lack of relativistic effects, the energy is heavily affected. We shouldn't just assume the entropy distribution and therefore the predicted CAS will be unaffected.

---

## Output Files

- Serenity output: `serenity/Po2_RHF_benchmark/serenity_Po2_RHF.o13110109`
- OpenMolcas output: `molcas/Po2_RHF_benchmark/molcas_Po2_RHF.o13110114`

---

## Related Documentation

- Error analysis for failed Po2 autoCAS run: [research/PO2_AUTOCAS_ERROR_ANALYSIS.md](../research/PO2_AUTOCAS_ERROR_ANALYSIS.md)
- Serenity relativistic support investigation: [research/relativistic/SERENITY_RELATIVISTIC_SUPPORT.md](../research/relativistic/SERENITY_RELATIVISTIC_SUPPORT.md)
- OpenMolcas orbital integration proposal: [research/relativistic/OPENMOLCAS_ORBITAL_INTEGRATION.md](../research/relativistic/OPENMOLCAS_ORBITAL_INTEGRATION.md)
