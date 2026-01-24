# Integrating OpenMolcas RHF Orbitals into autoCAS Workflow

**Goal**: Replace Serenity's non-relativistic SCF with OpenMolcas DKH2 SCF for heavy elements, while keeping Serenity's IBO localization and autoCAS entropy-based selection.

---

## Current autoCAS Workflow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ 1. Serenity: RHF calculation (non-relativistic)                             │
│    ↓                                                                        │
│ 2. Serenity: IBO localization                                               │
│    ↓                                                                        │
│ 3. Serenity: DOS orbital mapping across geometries                          │
│    ↓                                                                        │
│ 4. Serenity → OpenMolcas: Write orbitals to INPORB format                   │
│    ↓                                                                        │
│ 5. OpenMolcas: DMRG-CI for single-orbital entropies                         │
│    ↓                                                                        │
│ 6. autoCAS: Entropy-based active space selection                            │
│    ↓                                                                        │
│ 7. OpenMolcas: CASPT2 production calculation                                │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Problem**: Step 1 fails for heavy elements (Po, At, etc.) because non-relativistic orbital energies cause IBO to crash.

---

## Proposed Modified Workflow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ 1. OpenMolcas: RHF with DKH2 Hamiltonian                                    │
│    - Generates .ScfOrb file with correct relativistic orbital energies      │
│    ↓                                                                        │
│ 2. Serenity: Load orbitals from OpenMolcas INPORB/ScfOrb file               │
│    - Uses spy.ORBITAL_FILE_TYPES.MOLCAS reader                              │
│    ↓                                                                        │
│ 3. Serenity: IBO localization (energy cutoff now works correctly)           │
│    ↓                                                                        │
│ 4. Serenity: DOS orbital mapping across geometries                          │
│    ↓                                                                        │
│ 5. Serenity → OpenMolcas: Write localized orbitals back to INPORB           │
│    ↓                                                                        │
│ 6. OpenMolcas: DMRG-CI for single-orbital entropies                         │
│    ↓                                                                        │
│ 7. autoCAS: Entropy-based active space selection                            │
│    ↓                                                                        │
│ 8. OpenMolcas: CASPT2 production calculation                                │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Existing Code Support

### Serenity Can Already Read MOLCAS Orbital Files

From [serenity.py:232-254](../../autocas/scine_autocas/interfaces/serenity/serenity.py#L232):

```python
def load_or_write_molcas_orbitals(self, write=False):
    """Read or write orbitals from or to a molcas orbital file."""
    import qcserenity.serenipy as spy
    for i_sys, sys in enumerate(self.systems):
        loading_path = self.settings.molcas_orbital_files[i_sys]
        read = spy.OrbitalsIOTask_R(sys)
        read.settings.fileFormat = spy.ORBITAL_FILE_TYPES.MOLCAS
        read.settings.resetCoreOrbitals = False
        read.settings.replaceInFile = write
        read.settings.path = loading_path
        read.run()
```

**Key insight**: Serenity already supports `ORBITAL_FILE_TYPES.MOLCAS` for reading and writing!

### The `-s` Flag (load_orbitals)

From [cli.py](../../autocas/scine_autocas/io/cli.py):
```python
parser.add_option("-s", "--load_orbitals", dest="load_orbitals", action="store_true",
                  help="If true, paths to the Serenity system directories are expected...")
```

**Current behavior**: `-s` expects Serenity system directories (`.orbs.res.h5` files).

**What we need**: An option to load from OpenMolcas `.ScfOrb` files directly.

---

## Implementation Plan

### Step 1: Create OpenMolcas RHF Input Template

```
&GATEWAY
  Coord = po2.xyz
  Basis = ANO-RCC-VDZP
  Group = NoSym

&SEWARD
  Relativistic = Douglas-Kroll

&SCF
  Charge = 0
  Spin = 1
```

This generates a `.ScfOrb` file with DKH2-relativistic orbitals.

### Step 2: Modify autoCAS Configuration

Add new configuration option:

```yaml
# consistent_cas.configuration.yaml
use_external_orbitals: true
external_orbital_format: "MOLCAS"
external_orbital_files:
  - /path/to/system_0.ScfOrb
  - /path/to/system_1.ScfOrb
```

### Step 3: Modify Protocol to Skip Serenity SCF

In [protocol.py](../../autocas/scine_autocas/workflows/consistent_active_space/protocol.py), add logic:

```python
if configuration.use_external_orbitals:
    # Initialize Serenity with geometry only (no SCF)
    serenity = Serenity(molecules, settings)
    # Load orbitals from external files
    serenity.settings.molcas_orbital_files = configuration.external_orbital_files
    serenity.load_molcas_orbitals()
    # Skip serenity.calculate() - no SCF needed
else:
    serenity = Serenity(molecules, settings)
    serenity.load_or_write_molcas_orbitals()
    serenity.calculate()
```

### Step 4: Ensure Basis Set Consistency

**Critical**: OpenMolcas and Serenity must use identical basis sets!

| Aspect | OpenMolcas | Serenity |
|--------|------------|----------|
| Basis label | ANO-RCC-VDZP | ANO-RCC-VDZP |
| Contraction | Must match | Must match |
| Spherical/Cartesian | Usually spherical | Check settings |
| Basis function ordering | MOLCAS convention | Must match for orbital import |

### Step 5: Validate Orbital Import

After loading OpenMolcas orbitals into Serenity:
1. Check total energy matches (within numerical precision)
2. Verify orbital count matches
3. Confirm eigenvalues are read correctly

---

## Potential Issues

### 1. Basis Function Ordering

OpenMolcas and Serenity may use different orderings for:
- Angular momentum components (e.g., d orbitals: -2,-1,0,1,2 vs 0,1,-1,2,-2)
- Contracted functions within a shell

**Solution**: Serenity's MOLCAS reader should handle this, but needs verification.

### 2. Core Orbital Flags

When loading orbitals, the core orbital flags need to be set correctly:

```python
read.settings.resetCoreOrbitals = False  # Keep existing flags
# OR
read.settings.resetCoreOrbitals = True   # Recalculate based on energy cutoff
```

With DKH2 orbitals, the energy cutoff should work correctly.

### 3. Normalization Conventions

MOLCAS orbital files may use different normalization conventions. Verify:
- Overlap matrix S should give S·C·C^T = 1 for occupied orbitals
- Density matrix should integrate to correct electron count

---

## Testing Plan

### Test 1: Light Element Validation

1. Run standard autoCAS workflow for H2O (light element, no relativistic issues)
2. Run modified workflow: OpenMolcas SCF → Serenity IBO → autoCAS
3. Compare: orbital shapes, energies, active space selection

**Expected**: Results should be nearly identical (small numerical differences only).

### Test 2: Heavy Element (Po2)

1. Run OpenMolcas DKH2 SCF for Po2 at 3.0 Å
2. Import orbitals to Serenity
3. Run IBO localization
4. Verify: No crash, reasonable core-valence split

**Expected**: IBO completes without "core orbital is virtual" error.

### Test 3: Multi-Geometry Consistency

1. Generate OpenMolcas DKH2 orbitals for Po2 at 2.8, 3.0, 3.2 Å
2. Import all to Serenity
3. Run IBO and DOS mapping
4. Verify: Orbital mapping succeeds across geometries

---

## Files to Modify

| File | Modification |
|------|-------------|
| `autocas/scine_autocas/workflows/consistent_active_space/configuration.py` | Add `use_external_orbitals`, `external_orbital_files` options |
| `autocas/scine_autocas/workflows/consistent_active_space/protocol.py` | Add logic to skip Serenity SCF when using external orbitals |
| `autocas/scine_autocas/io/cli.py` | Add `--external-orbitals` command line flag |
| New: `scripts/generate_molcas_scf.py` | Script to generate OpenMolcas RHF inputs |

---

## Alternative: Use Serenity Only for Localization

A minimal approach:
1. Run OpenMolcas DKH2 SCF (generates `.ScfOrb`)
2. Write a standalone script that:
   - Loads `.ScfOrb` into Serenity
   - Runs IBO localization
   - Writes back to `.ScfOrb`
3. Continue with OpenMolcas DMRG-CI and autoCAS

This avoids modifying the autoCAS codebase but requires manual orbital file management.

---

## References

- Serenity OrbitalsIOTask: [serenity/src/tasks/OrbitalsIOTask.cpp](../../serenity/src/tasks/OrbitalsIOTask.cpp)
- MOLCAS orbital file format: OpenMolcas documentation, INPORB section
- autoCAS Serenity interface: [autocas/scine_autocas/interfaces/serenity/serenity.py](../../autocas/scine_autocas/interfaces/serenity/serenity.py)
