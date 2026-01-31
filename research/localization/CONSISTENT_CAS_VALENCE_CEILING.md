# Why CAS(12,8) Cannot Expand: The Valence Ceiling in autoCAS

**Date**: 2026-01-31
**Status**: Analysis complete
**Conclusion**: The `consistent_cas_algorithm` is structurally unable to exceed `CAS(12,8)` for Po₂ because that **is** the full valence space as defined by the `Elements` class. The union operation over geometries cannot add orbitals that are not in the valence space to begin with.

---

## 1. The Problem

Running the `consistent_cas_algorithm` on Po₂ dissociation (15 geometries, 2.1-10.0 A) produces `CAS(12,8)` for every geometry:

```
final CAS(e, o):  (12, 8)
final cas indices: [78, 79, 80, 81, 82, 83, 84, 85]
final occupation:  [2, 2, 2, 2, 2, 2, 0, 0]
```

The active space is identical across all geometries. The `consistent_cas_algorithm`'s union step produces no expansion. This raises the question: is CAS(12,8) physically adequate, or is the algorithm too restrictive?

---

## 2. Root Cause: The Elements Class

The hard ceiling comes from the `Elements` class in:
`autocas/scine_autocas/utils/chemical_elements.py:739-745`

```python
{
    "name": "Po",
    "atomic number": 84,
    "number of core orbitals": 39,
    "number of valence orbitals": 4,
    "core orbitals": ["1s", "2s", "2p", "3s", "3p", "3d", "4s", "4p", "4d", "4f", "5s", "5p", "5d"],
    "valence orbitals": ["6s", "6p"],
}
```

For Po₂:
- Core orbitals per atom: 39 → total core: 78
- Valence orbitals per atom: 4 (one 6s + three 6p) → total valence: **8**
- Valence electrons per atom: 6 (6s² 6p⁴) → total: **12**

**CAS(12,8) is the maximum the algorithm can ever produce for Po₂.**

---

## 3. How the Initial CAS is Built

The initial active space is constructed in `active_space_handler.py:133-189`:

```python
def _make_valence_cas(self):                    # line 133
    orbital_indices = self._make_valence_indices()
    occupation = self._make_valence_occupation()
    self._set_valence_cas(ActiveSpace(occupation, orbital_indices))

def _make_valence_indices(self):                # line 174
    orbital_indices = []
    for i in range(self._molecule.valence_orbitals):  # = 8 for Po₂
        orbital_indices.append(self._molecule.core_orbitals + i)  # indices 78-85
    return orbital_indices

def _make_valence_occupation(self):             # line 139
    n_electrons = self._molecule.electrons - 2 * self._molecule.core_orbitals  # = 12
    # ...fills orbitals with 2, 1, or 0 based on spin multiplicity
```

The initial CAS for Po₂ is always `CAS(12,8)` with indices `[78,79,80,81,82,83,84,85]` and occupation `[2,2,2,2,2,2,0,0]`.

---

## 4. The Entropy Plateau Detection Cannot Reduce It

autoCAS then runs a DMRG calculation on this initial CAS and looks for entropy plateaus to **reduce** the space (`autocas.py:261-340`):

```python
def get_active_space(self, s1_entropy, ...):    # line 261
    self._check_single_reference(s1_entropy, force_cas)  # line 312
    if self._make_active_space():               # line 320 — plateau search
        return self._pretty_return()            # found smaller CAS
    # ...fallback: exclude low-entropy orbitals
```

For Po₂, the plateau detection either:
1. **Finds a plateau** within the 8-orbital space → selects a subset (e.g., CAS(8,5))
2. **Finds no plateau** → keeps full CAS(12,8)
3. **Finds all entropies are low** → raises `SingleReferenceException` (caught by `--force-cas`)

In the scaling test output, `CAS(12,8)` with `final s1: []` (empty entropy) and `force_cas=True` suggests the algorithm defaulted to the full valence space because entropy analysis didn't find multiconfigurational character, and `--force-cas` prevented the exception.

---

## 5. Why the Union Step Does Nothing

The `combine_active_spaces` function in `cas_combination.py:39-92` takes the union of active orbital groups across geometries:

```python
def combine_active_spaces(occupations, active_spaces, orbital_groups):
    orbital_to_group = transform_orbital_groups(orbital_groups)  # line 70
    active_orbital_groups = []
    for i_sys, (occupation, active_space) in enumerate(zip(occupations, active_spaces)):
        for i_orb, occ in zip(active_space, occupation):
            i_group = orbital_to_group[i_orb, i_sys]   # line 76
            if i_group not in active_orbital_groups:    # line 77
                active_orbital_groups.append(i_group)   # line 78 — UNION
    # ...build combined CAS from active groups (lines 86-91)
```

The union operates at the **orbital group** level (from Serenity's DOS mapping). If geometry 1 selects orbital group A and geometry 2 selects group B, both are included in the final CAS for all geometries.

**But for Po₂**: every geometry selects the same 8 valence orbitals → the same orbital groups → the union is identical to each individual CAS. Even if different geometries selected different subsets of the 8 valence orbitals, the union could at most reach 8.

---

## 6. The Orbital Mapping Constraint

The DOS orbital mapping (`serenity.py:338-363`) maps localized orbitals between geometries:

```python
def build_orbital_map(self, fragments):         # line 338
    gdos = spy.GeneralizedDOSTask_R(self.systems, fragments)
    gdos.settings.similarityLocThreshold = self.settings.partitioning_thresholds
    gdos.settings.mapVirtuals = self.settings.localize_virtuals  # line 355
    gdos.settings.bestMatchMapping = self.settings.optimized_mapping
    gdos.run()
    return gdos.getOrbitalGroupIndices(), gdos.getUnmappableOrbitalGroupIndices()
```

The mapping creates groups of "indistinguishable" orbitals across geometries. Only orbitals that can be mapped are included in the combination. **Unmappable orbitals** (those that change character across geometries) are excluded by default (`configuration.py:67`):

```python
self.unmappable: bool = False  # default: DO NOT include unmappable orbitals
```

This is a secondary limitation: even if we expanded the valence space, orbitals that change character along the dissociation curve would be dropped unless `--always-include-unmapables` is passed. For a dissociating dimer, orbital character changes significantly, so unmappable orbitals could be important.

However, the `--always-include-unmapables` flag adds unmappables to the CAS **in addition to** the mapped union (`protocol.py:175-190`):

```python
if configuration.unmappable:
    for cas_index, cas_occ, u_occ, u_virt in zip(...):
        for i in u_occ:
            if i not in cas_index:
                cas_index.append(i)    # line 185 — add occupied unmappable
                cas_occ.append(occ)
        for i in u_virt:
            if i not in cas_index:
                cas_index.append(i)    # line 189 — add virtual unmappable
                cas_occ.append(0)
```

This **can** expand the CAS beyond the valence space — but only if unmappable orbitals exist. For Po₂ with only 8 valence orbitals and the mapping being straightforward (symmetric dimer), this is unlikely to help.

---

## 7. What Would Be Needed for a Larger CAS

### Option A: Expand the Elements class valence definition for Po

Change `chemical_elements.py:739-745` to include 5d in the valence space:

```python
{
    "name": "Po",
    "number of core orbitals": 34,       # was 39
    "number of valence orbitals": 9,      # was 4 (add 5d: 5 orbitals)
    "core orbitals": ["1s", "2s", "2p", "3s", "3p", "3d", "4s", "4p", "4d", "4f", "5s", "5p"],
    "valence orbitals": ["5d", "6s", "6p"],
}
```

This would give Po₂: CAS(22, 18) initially — likely too large for plain CASSCF but feasible with DMRG. The entropy plateau analysis would then select a meaningful subset.

**Pros**: Stays within autoCAS framework, minimal code changes
**Cons**: CAS(22,18) initial space requires DMRG for entropy evaluation; larger valence space changes IBO localization behavior (more virtual valence orbitals); may need the `large_active_space` protocol which subdivides and recombines

### Option B: Use ROSE instead of Serenity

ROSE (Reiher's Orbital Selection and Evaluation) uses a different orbital generation strategy:
- PySCF-based with scalar-X2C relativistic Hamiltonian
- Does not depend on IBO/MINAO for orbital classification
- Can define active spaces based on atomic orbital character analysis
- Not constrained by a predefined `Elements` table

**Pros**: More flexible active space; avoids MINAO limitations entirely; PySCF has better heavy element support
**Cons**: Requires setting up ROSE; different orbital mapping scheme; may lose IBO localization quality

### Option C: Manual override of CAS

The `run_autocas` function (`run_autocas.py:130-164`) could be bypassed to provide a custom initial CAS. However, this defeats the purpose of automated CAS selection.

---

## 8. Why This Matters Physically

For Po₂ dissociation:
- Near equilibrium (~2.5 A): The 6s and 6p valence space may suffice for the ground state, though SO coupling mixes states
- At dissociation (>5 A): The 5d shell could become important as the bonding changes character
- For SO-CASSI: spin-orbit coupling mixes states of different spatial symmetry; a richer active space gives more states to couple

The fact that every geometry produces the same CAS(12,8) with empty `s1` entropy suggests:
1. The DMRG calculation within the valence space doesn't find significant multiconfigurational character, OR
2. The `force_cas` flag is overriding the single-reference detection, returning the full valence space without entropy-guided reduction

Either way, the `consistent_cas_algorithm` is doing nothing useful here — it's just returning the chemically predefined valence space. The bond dimension / sweep parameters (`consistent_cas_algorithm` tuning) cannot help because the valence space ceiling is the binding constraint.

---

## 9. Summary

| Aspect | Current State | Impact |
|--------|--------------|--------|
| Po valence definition | 4 orbitals (6s, 6p) | CAS ceiling = 8 orbitals for Po₂ |
| CAS(12,8) | = full valence space | Plateau detection and union cannot expand |
| Entropy `s1 = []` | No entropy computed or all zero | `force_cas` returns full valence by default |
| Union across geometries | Same CAS everywhere | No expansion possible |
| Orbital mapping | Irrelevant at ceiling | Groups are all active regardless |

**Bottom line**: The `consistent_cas_algorithm` is structurally capped at CAS(12,8) for Po₂. To get a physically richer active space, either expand the `Elements` class definition for Po (include 5d) or switch to ROSE which can define larger active spaces without this ceiling.
