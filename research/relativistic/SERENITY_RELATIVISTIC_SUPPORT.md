# Serenity Relativistic Support Investigation

**Date**: 2026-01-24
**Conclusion**: Serenity does NOT support scalar relativistic Hamiltonians (DKH, X2C, ZORA)

---

## Search Results

### Scalar Relativistic Hamiltonians

Searched for: `X2C`, `DKH`, `Douglas-Kroll`, `ZORA`, `relativistic`

```bash
grep -ri "X2C\|DKH\|Douglas.Kroll\|ZORA" serenity/src/
```

**Result**: No matches for actual relativistic Hamiltonian implementations.

The only matches were:
- `m05x2c`, `m06x2c` - These are DFT functional names (M05-2X, M06-2X), not X2C Hamiltonian
- One comment in `SuperpositionOfAtomicPotentials.h`:
  ```cpp
  // The data used is the non-relativistic CAPX SAP guess
  ```

This confirms Serenity uses **non-relativistic Hamiltonians only**.

---

## ECP Support (Alternative to Scalar Relativistic)

Serenity DOES support Effective Core Potentials (ECPs):

```cpp
// From AtomicDensityGuessCalculator.cpp
bool usesECPs = atom->usesECP();

// From SuperpositionOfAtomicPotentials.cpp
fock -= system->getOneElectronIntegralController()->getECPIntegrals();
```

### ECP as Workaround?

ECPs can partially account for scalar relativistic effects by:
1. Replacing core electrons with an effective potential
2. Using relativistically-optimized ECP parameters

**However**, ECPs have limitations:
- Core-valence correlation is lost
- Semi-core electrons may not be well-described
- For autoCAS, we need ALL electrons for entropy-based selection

**Verdict**: ECPs are NOT suitable for autoCAS4HE where we want all-electron treatment.

---

## What Would Be Needed to Add Relativistic Support

### Option 1: DKH2 (Douglas-Kroll-Hess, 2nd order)

**Implementation complexity**: Medium

Would require:
1. DKH transformation of one-electron integrals (kinetic + nuclear attraction)
2. Modified Fock matrix construction
3. Transformation matrices for property calculations

**Files to modify**:
- `src/integrals/OneElectronIntegralController.cpp` - Add DKH integrals
- `src/potentials/HCorePotential.cpp` - Use DKH-transformed H_core
- New file: `src/integrals/DKHTransformation.cpp`

### Option 2: X2C (eXact 2-Component)

**Implementation complexity**: High

Would require:
1. Dirac equation solution for atomic orbitals
2. X2C decoupling transformation
3. Picture-change corrections for properties

### Option 3: ZORA (Zeroth-Order Regular Approximation)

**Implementation complexity**: Low-Medium

Would require:
1. Modified kinetic energy operator: T_ZORA = p · (c²/(2c² - V)) · p
2. Integration of ZORA potential on grid

**Note**: ZORA is geometry-dependent (gauge problem) which may complicate gradient calculations.

---

## Recommendation

Since adding scalar relativistic support to Serenity is a significant undertaking, the recommended approach is:

**Use OpenMolcas for SCF with DKH2, then import orbitals to Serenity for IBO localization.**

See [OPENMOLCAS_ORBITAL_INTEGRATION.md](OPENMOLCAS_ORBITAL_INTEGRATION.md) for details.

---

## References

1. Douglas, M.; Kroll, N. M. "Quantum electrodynamical corrections to the fine structure of helium" *Ann. Phys.* 1974, 82, 89-155.
2. Hess, B. A. "Relativistic electronic-structure calculations employing a two-component no-pair formalism" *Phys. Rev. A* 1986, 33, 3742.
3. Iliaš, M.; Saue, T. "An infinite-order two-component relativistic Hamiltonian by a simple one-step transformation" *J. Chem. Phys.* 2007, 126, 064102.
