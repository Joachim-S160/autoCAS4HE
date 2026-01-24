# IBO Energy Cutoff Analysis: Why Core-Valence Classification Fails for Heavy Elements

**Related issue**: Po2 autoCAS crash during IBO localization
**Key finding**: The -5.0 Hartree energy cutoff breaks down without relativistic treatment

---

## How Core Orbital Count (N=60) is Determined

### The Energy Cutoff Mechanism

The IBO localization in autoCAS determines core vs. valence orbitals using an **energy cutoff** of -5.0 Hartree:

1. **autoCAS sets** `splitValenceAndCore = True` ([serenity.py:204](../../autocas/scine_autocas/interfaces/serenity/serenity.py#L204))

2. **Default Serenity settings**:
   - `useEnergyCutOff = True`
   - `energyCutOff = -5.0` Hartree
   ([LocalizationTask.h:41-42](../../serenity/src/tasks/LocalizationTask.h#L41))

3. **Classification logic** ([OrbitalController.cpp:714-728](../../serenity/src/data/OrbitalController.cpp#L714)):
   ```cpp
   for (unsigned int iOrb = 0; iOrb < eigenvalues_spin.size(); ++iOrb) {
     if (eigenvalues_spin(iOrb) < energyCutOff) {   // < -5.0 Hartree
       orbitalFlags_spin(iOrb) = 1;                 // Mark as core
     }
   }
   ```

4. **For non-relativistic Po2**:
   - 60 orbitals have ε < -5.0 Hartree → core
   - 24 orbitals have ε ≥ -5.0 Hartree → valence
   - Total: 84 occupied orbitals (168 electrons / 2)

### Why This Fails for Heavy Elements

The -5.0 Hartree cutoff assumes orbital energies follow a "normal" ordering where:
- Core orbitals have very negative energies (ε << -5.0)
- Valence orbitals have moderately negative energies (ε ~ -1 to -5.0)
- Virtual orbitals have positive or near-zero energies

**Without relativistic effects** (Serenity's current limitation):
- Inner shell orbitals of heavy elements have **wrong energies**
- Some "core" orbitals end up with abnormally high energies
- The energy-based classification breaks down
- Crash occurs when Rydberg assignment finds a "core" orbital at high energy

---

## Requirements for a Better Energy Cutoff

### The Core Problem

A fixed energy cutoff (-5.0 Hartree) cannot work universally because:

| Element Range | Typical Core-Valence Gap | -5.0 Cutoff Works? |
|--------------|--------------------------|-------------------|
| Light (Z < 36) | Clear, well-separated | Yes |
| Transition metals (Z = 21-30, 39-48, 72-80) | Moderate | Usually |
| Post-transition/heavy (Z > 80) | Distorted without relativity | No |

### Potential Improvements

#### 1. Element-Aware Energy Cutoff

Instead of a fixed -5.0 Hartree, use element-dependent cutoffs:

```cpp
double getElementAwareCutoff(unsigned int atomicNumber) {
    if (atomicNumber <= 36) return -5.0;      // Light elements
    if (atomicNumber <= 54) return -10.0;     // 4d transition metals
    if (atomicNumber <= 86) return -20.0;     // 5d/6p elements (needs tuning)
    return -50.0;                              // Actinides
}
```

**Problem**: Still assumes non-relativistic energies are meaningful, which they aren't for Z > 50.

#### 2. Core Count by Atomic Configuration

Instead of energy cutoff, use the known number of core electrons per element:

```cpp
// Already exists in Serenity: NUMBER_OF_CORE_ELECTRONS[Z]
// For Po (Z=84): 68 core electrons → 34 core orbitals per atom
unsigned int nCoreOrbitals = geometry->getNumberOfCoreElectrons() / 2;
```

**Problem**: This is a "chemical" definition, not an energy-based one. May not align with orbital ordering in non-relativistic calculation.

#### 3. Relativistic Orbital Energies (The Real Solution)

The only robust solution is to use **scalar relativistic Hamiltonians**:
- DKH2 (Douglas-Kroll-Hess, 2nd order)
- X2C (eXact 2-Component)
- ZORA (Zeroth-Order Regular Approximation)

With correct relativistic energies:
- Core orbitals have properly contracted, low energies
- The -5.0 Hartree cutoff (or similar) works correctly
- IBO localization proceeds without conflict

---

## Research Directions: Relativistic Localization

### Questions to Investigate

1. **Does Serenity support any relativistic Hamiltonians?**
   - See [../relativistic/SERENITY_RELATIVISTIC_SUPPORT.md](../relativistic/SERENITY_RELATIVISTIC_SUPPORT.md)
   - **Answer: No**

2. **Can IBO work with relativistic orbitals from external codes?**
   - Use OpenMolcas DKH2 orbitals
   - Convert to Serenity format
   - Apply IBO localization to those orbitals
   - See [../relativistic/OPENMOLCAS_ORBITAL_INTEGRATION.md](../relativistic/OPENMOLCAS_ORBITAL_INTEGRATION.md)

3. **Are there relativistic variants of IBO?**
   - Literature search: "relativistic intrinsic bond orbitals"
   - Check if IAO projection is valid with 2-component wavefunctions

4. **What about 2-component localization?**
   - X2C and DKH2 give scalar (1-component) orbitals - should work with standard IBO
   - Full 4-component Dirac methods give spinors - need modified localization

### Relevant Literature

- Knizia, G. "Intrinsic Atomic Orbitals: An Unbiased Bridge between Quantum Theory and Chemical Concepts" *J. Chem. Theory Comput.* 2013, 9, 4834-4843.
- Peng, D.; Reiher, M. "Exact decoupling of the relativistic Fock operator" *Theor. Chem. Acc.* 2012, 131, 1081.

### Proposed Workflow for Heavy Elements

```
┌─────────────────────────────────────────────────────────────┐
│ 1. OpenMolcas: RHF with DKH2 Hamiltonian                    │
│    → Correct relativistic orbital energies                  │
│    → Proper core-valence separation                         │
├─────────────────────────────────────────────────────────────┤
│ 2. Convert orbitals: OpenMolcas → Serenity format           │
│    → Serenity already supports MOLCAS orbital format        │
│    → Match basis set ordering conventions                   │
├─────────────────────────────────────────────────────────────┤
│ 3. Serenity: IBO localization on imported orbitals          │
│    → Energy cutoff now works correctly                      │
│    → IBO gives chemically meaningful localized orbitals     │
├─────────────────────────────────────────────────────────────┤
│ 4. autoCAS: Entropy-based CAS selection                     │
│    → Use localized relativistic orbitals                    │
│    → DMRG-CI for entanglement analysis                      │
└─────────────────────────────────────────────────────────────┘
```
