# Po2 autoCAS Error Analysis

**Error**: `RuntimeError: A core orbital is assigned to be virtual. Something is wrong here!`
**Source**: [serenity/src/data/OrbitalController.cpp:694](../serenity/src/data/OrbitalController.cpp#L694)

---

## Timeline of the Failed Run

1. **SCF for system_0 (Po2 at 2 Å)**: Converged in 17 cycles, ~4.5 hours, E = -34701.36 Hartree
2. **SCF for system_1 (Po2 at 4 Å)**: Converged in 18 cycles, ~4.2 hours, E = -34698.89 Hartree
3. **IBO Localization starts**:
   - Output: `Number of core-like orbitals: 60`
   - Output: `Core-like orbitals will be localized separately.`
4. **CRASH**: `A core orbital is assigned to be virtual`

---

## Code Analysis

### Where the error is thrown

[OrbitalController.cpp:676-699](../serenity/src/data/OrbitalController.cpp#L676):

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

[OrbitalController.cpp:640-665](../serenity/src/data/OrbitalController.cpp#L640) - `getCoreOrbitalsByEigenvalue()`:

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

[AtomType.cpp:196-230](../serenity/src/geometry/AtomType.cpp#L196):

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

[LocalizationTask.cpp:111-135](../serenity/src/tasks/LocalizationTask.cpp#L111):

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

---

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

---

## Potential Fixes

### 1. Check if Serenity supports X2C/DKH
See [relativistic/SERENITY_RELATIVISTIC_SUPPORT.md](relativistic/SERENITY_RELATIVISTIC_SUPPORT.md) - **Answer: No**

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
See [localization/IBO_VS_OTHER_LOCALIZATION.md](localization/IBO_VS_OTHER_LOCALIZATION.md) for why we prefer IBO.

### 4. Bypass Serenity for orbital preparation
Use OpenMolcas orbitals via the `-s` flag.
See [relativistic/OPENMOLCAS_ORBITAL_INTEGRATION.md](relativistic/OPENMOLCAS_ORBITAL_INTEGRATION.md) for implementation details.
