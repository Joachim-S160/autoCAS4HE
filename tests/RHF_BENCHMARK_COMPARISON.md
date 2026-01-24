# Po2 RHF Benchmark Comparison: Serenity vs OpenMolcas

**Date:** 2026-01-24
**System:** Po2 at 2.0 Å bond length
**Basis:** ANO-RCC-VDZP (136 basis functions)
**HPC:** VSC Hortense, 16 cores, 32 GB RAM

## Timing Results

| Code | Wall Time | SCF Cycles |
|------|-----------|------------|
| **OpenMolcas** | **2.25 minutes** (134.91 s) | 5 |
| **Serenity** | **288 minutes** (4.8 hours) | 17 (Po2) + 12 (Po atom) |

**OpenMolcas is ~128x faster than Serenity for this calculation.**

## Energy Results

| Code | Total Energy (Hartree) | Relativistic Treatment |
|------|------------------------|------------------------|
| **OpenMolcas** | -44341.6825837401 | DKH2 (Douglas-Kroll-Hess order 2) |
| **Serenity** | -34701.3606231649 | Non-relativistic |

**Energy difference: ~9640 Hartree** - due to scalar relativistic effects!

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

## Files

- Serenity output: `tests/serenity/Po2_RHF_benchmark/serenity_Po2_RHF.o13110109`
- OpenMolcas output: `tests/molcas/Po2_RHF_benchmark/molcas_Po2_RHF.o13110114`

## Next Steps

1. Investigate if Serenity can use scalar relativistic treatment (X2C, DKH)
2. Test autoCAS with `-s` flag to use pre-computed OpenMolcas orbitals (needs script adapatations, autocas expects serenity type files)
3. Check if IBO is still appropriate
4. Check if any procedures down the line (orbital mapping eg) also need adaptations regarding relativistic effects

---

# Po2 autoCAS Error Analysis

## Error Message
```
RuntimeError: A core orbital is assigned to be virtual. Something is wrong here!
```

**Source:** [serenity/src/data/OrbitalController.cpp:694](serenity/src/data/OrbitalController.cpp#L694)

## Timeline of the Failed Run

1. **SCF for system_0 (Po2 at 2 Å)**: Converged in 17 cycles, ~4.5 hours, E = -34701.36 Hartree
2. **SCF for system_1 (Po2 at 4 Å)**: Converged in 18 cycles, ~4.2 hours, E = -34698.89 Hartree
3. **IBO Localization starts**:
   - Output: `Number of core-like orbitals: 60`
   - Output: `Core-like orbitals will be localized separately.`
4. **CRASH**: `A core orbital is assigned to be virtual`

## Code Analysis

### Where the error is thrown

[OrbitalController.cpp:676-699](serenity/src/data/OrbitalController.cpp#L676):

```cpp
void OrbitalController<SCFMode>::setRydbergOrbitalsByNumber(unsigned int nRydbergOrbitals) {
  // ...
  for_spin(orbitalFlags, eigenvalues) {
    Eigen::VectorXd eps = eigenvalues_spin;
    for (unsigned int iRydberg = 0; iRydberg < nRydbergOrbitals; ++iRydberg) {
      int maxIndex;
      eps.maxCoeff(&maxIndex);           // Find orbital with HIGHEST energy
      eps[maxIndex] = -infinity;          // Mark it so we don't select again
      if (orbitalFlags_spin[maxIndex] == 1) {   // Flag 1 = core orbital
        throw SerenityError("A core orbital is assigned to be virtual. Something is wrong here!");
      }
      orbitalFlags_spin[maxIndex] = 2;    // Flag 2 = Rydberg/virtual
    }
  };
}
```

### How core orbitals are assigned

[OrbitalController.cpp:640-665](serenity/src/data/OrbitalController.cpp#L640) - `getCoreOrbitalsByEigenvalue()`:

```cpp
// Assigns core orbitals by finding the N orbitals with LOWEST eigenvalues
for (unsigned int iCore = 0; iCore < nCoreOrbitals_spin; ++iCore) {
  int minIndex;
  eps.minCoeff(&minIndex);           // Find orbital with LOWEST energy
  eps[minIndex] = infinity;           // Mark it
  orbitalFlags_spin[minIndex] = 1;    // Flag as core
}
```

### How minimal basis size determines core count

[AtomType.cpp:196-230](serenity/src/geometry/AtomType.cpp#L196):

```cpp
unsigned int AtomType::getMinimalBasisSize() const {
  // ...
  else if (_psePosition < 87) {   // Elements 57-86 (lanthanides + 6th period)
    return 43;                     // 43 minimal basis functions per atom
  }
  // ...
}
```

For Po (Z=84): minimal basis = 43 per atom → 86 for Po2

### The IBO localization flow

[LocalizationTask.cpp:111-135](serenity/src/tasks/LocalizationTask.cpp#L111):

```cpp
if (settings.useEnergyCutOff) {
  setCoreOrbitalsByEnergyCutOff(settings.energyCutOff);
}
else if (settings.nCoreOrbitals != infinity) {
  setCoreOrbitalsByNumber(settings.nCoreOrbitals);
}

// Output we saw:
OutputControl::nOut << "  Number of core-like orbitals: "
                    << nOcc_spin - valenceRange_spin.size();
// For Po2: 84 occupied - 24 valence = 60 core-like
```

## The Root Cause

### Non-relativistic orbital energies are wrong for heavy elements

For Po2 with **non-relativistic HF**:
- Orbital energies don't follow the expected order
- Some deep "core" orbitals (by chemical intuition) may have abnormally high energies
- The energy-based classification breaks down

### The conflict:

| Step | Uses Energy | Assumption |
|------|------------|------------|
| Assign core orbitals | LOWEST energies | Core = deep, low energy |
| Assign Rydberg orbitals | HIGHEST energies | Virtual = diffuse, high energy |

With non-relativistic treatment of Z=84:
- An orbital classified as "core" (lowest energies) ends up having one of the highest energies
- When the algorithm tries to mark Rydberg orbitals, it finds a "core" orbital at high energy
- Sanity check fails → crash

### Why relativistic effects matter

| Effect | Non-relativistic | With DKH2 |
|--------|-----------------|-----------|
| 1s orbital | Too high energy | Correctly contracted, lower energy |
| Outer d/f orbitals | Wrong ordering | Correct ordering |
| Core-valence gap | May be inverted | Physically correct |

## Potential Fixes

### 1. Check if Serenity supports X2C/DKH
Search the codebase for relativistic options:
```bash
grep -r "X2C\|DKH\|Douglas\|Kroll\|relativistic" serenity/src/
```

### 2. Skip localization entirely
In autoCAS serenity interface, check `settings.skip_localization`:
```python
# serenity/serenity.py line 83
self.skip_localization: bool = False  # Try setting to True
```

### 3. Use different localization method
IBO specifically uses minimal basis IAOs. Try Foster-Boys or Pipek-Mezey:
```python
# serenity/serenity.py line 65
self.localisation_method: str = "IBO"
# Options: PIPEK_MEZEY, BOYS, EDMINSTON_RUEDENBERG, IBO
```

### 4. Bypass Serenity for orbital preparation
Use OpenMolcas orbitals via the `-s` flag (requires format conversion)
