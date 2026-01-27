# Virtual Orbital Localization: Required or Not for autoCAS?

**Created**: 2026-01-27
**Status**: Research Analysis
**Context**: Testing PM/FB localization for Po2 where virtual localization is not supported

---

## Executive Summary

Virtual orbital localization is **not strictly required** for autoCAS to function, but its absence affects:
1. The quality of orbital mapping between structures
2. Whether virtual orbitals can be reliably identified across geometries
3. The completeness of the combined active space

For heavy elements like Po2, using PM/FB localization (without virtual localization) is **likely acceptable** because:
- The active space is dominated by valence orbitals
- Unmappable virtuals can be handled by the `-u` flag (include all unmappables)
- CASSCF/DMRGSCF calculations are geometry-local anyway

---

## How Localization Affects the autoCAS Workflow

### The Workflow Steps

```
1. Serenity SCF (or load external orbitals)
2. Orbital Localization (IBO/PM/FB)
   └── Occupied: Always localized
   └── Virtual: Only with IBO/IAO (if localize_virtuals=True)
3. Direct Orbital Selection (DOS) Mapping
   └── mapVirtuals = localize_virtuals setting
   └── Creates orbital_map and unmappable_orbitals
4. autoCAS Entropy Selection (per geometry)
5. combine_active_spaces() using orbital_map
   └── Union of all selected orbitals
   └── unmappable orbitals handled separately
```

### What `localize_virtuals` Controls

From [serenity.py:351](../../autocas/scine_autocas/interfaces/serenity/serenity.py#L351):
```python
gdos.settings.mapVirtuals = self.settings.localize_virtuals
```

When `localize_virtuals = False`:
- Virtual orbitals remain canonical (delocalized)
- Virtual orbitals are NOT included in the DOS mapping
- All virtuals become "unmappable" between structures

---

## Core vs Valence Classification in Serenity

### Energy-Based Cutoff

Serenity uses an energy cutoff (default: -5.0 Hartree) to separate core from valence orbitals:

```cpp
// LocalizationTask.h default
energyCutOff = -5.0  // Hartree
```

Orbitals with ε < -5.0 Ha are classified as **core** and treated separately.

### Implications for Heavy Elements

| Scenario | Core Classification | Effect on autoCAS |
|----------|-------------------|------------------|
| More orbitals classified as core than chemical picture | Core orbitals excluded from localization and mapping | OK - conservative, autoCAS won't select deep core anyway |
| Fewer orbitals classified as core than chemical picture | Some core orbitals treated as valence | **Problem** - may pollute the mapping with irrelevant orbitals |

For DKH2 relativistic orbitals (Po2):
- Core orbitals have very negative energies (1s at -3431 Ha for Po)
- The -5.0 Ha cutoff correctly separates core from valence
- **This should work correctly** with external DKH2 orbitals

---

## The Orbital Mapping (DOS) Algorithm

### How It Works

The Direct Orbital Selection (DOS) algorithm maps orbitals between structures by comparing:
1. **Localization similarity**: How similarly localized on the same atoms
2. **Kinetic energy similarity**: Same kinetic energy character

From [GeneralizedDOSTask.h:135-136](../../serenity/src/tasks/GeneralizedDOSTask.h#L135):
```cpp
// mapVirtuals: If true, the virtual orbitals are considered in the
//              orbital mapping. By default false.
```

### What Happens Without Virtual Mapping

```
Structure 0:           Structure 1:
Occ 0  ←→  Occ 0      (mapped)
Occ 1  ←→  Occ 1      (mapped)
...
Virt 0  ×  Virt 0     (NOT mapped)
Virt 1  ×  Virt 1     (NOT mapped)
```

Virtual orbitals exist in `unmappable_orbitals` list instead.

---

## Impact on Active Space Selection

### autoCAS Entropy-Based Selection

For each geometry individually, autoCAS:
1. Runs DMRG-CI with trial active space
2. Calculates single-orbital entropy
3. Selects orbitals with high entropy → chemically active

This step works **independently of localization method**.

### CAS Combination Step

From [cas_combination.py:39-41](../../autocas/scine_autocas/cas_selection/cas_combination.py#L39):
```python
def combine_active_spaces(occupations, active_spaces, orbital_groups):
    """Combine multiple active spaces through orbital maps."""
```

Without virtual mapping:
- If autoCAS selects virtual orbital V on geometry 0
- The corresponding virtual V' on geometry 1 is **not known**
- V goes into `unmappable_orbitals`

### Handling Unmappable Orbitals

From [protocol.py:167-183](../../autocas/scine_autocas/workflows/consistent_active_space/protocol.py#L167):
```python
if configuration.unmappable:
    # Include ALL unmappable occupied and virtual orbitals
    for i in u_occ:
        if i not in cas_index:
            cas_index.append(i)
            cas_occ.append(occ)
    for i in u_virt:
        if i not in cas_index:
            cas_index.append(i)
            cas_occ.append(0)
```

**Option 1**: `-u` flag includes all unmappable orbitals
- Conservative: larger CAS
- Safe: won't miss important orbitals
- May include irrelevant orbitals

**Option 2**: Default (no `-u` flag)
- Only mapped orbitals are combined
- May miss important virtual orbitals on some geometries
- Smaller, more targeted CAS

---

## Recommendations for Heavy Elements (Po2)

### Use PM/FB Without Virtual Localization

Given that:
1. IBO fails for Po2 (MINAO too small)
2. PM/FB don't support virtual localization
3. The autoCAS entropy selection works per-geometry anyway

**Recommendation**: Proceed with PM or FB localization and handle unmapped virtuals:

```bash
# Option A: Include all unmappables (safer, larger CAS)
scine_autocas_consistent_active_space -e -o "orb1.h5,orb2.h5" \
    -L PIPEK_MEZEY -u -b ANO-RCC-VDZP mol1.xyz mol2.xyz

# Option B: Trust the occupied mapping (smaller CAS)
scine_autocas_consistent_active_space -e -o "orb1.h5,orb2.h5" \
    -L PIPEK_MEZEY -b ANO-RCC-VDZP mol1.xyz mol2.xyz
```

### Why This Is Acceptable

1. **Active spaces are usually dominated by valence electrons**
   - Bonding/antibonding σ, π orbitals
   - These are occupied or low-lying virtuals
   - High-energy Rydberg-like virtuals rarely important

2. **CASSCF/DMRGSCF is geometry-local**
   - Each geometry optimizes its own orbitals
   - The mapping is mainly for consistency across PES
   - Small inconsistencies in virtual space are tolerable

3. **Entropy selection will find important virtuals**
   - Even without mapping, autoCAS will select important virtuals
   - The `-u` flag ensures they're included in final CAS

---

## Comparison: With vs Without Virtual Localization

| Aspect | IBO (with virtuals) | PM/FB (no virtuals) |
|--------|---------------------|---------------------|
| Occupied localization | Yes | Yes |
| Virtual localization | Yes | No |
| Orbital mapping quality | High | Lower (only occupied) |
| Unmappable orbitals | Few | Many (all virtuals) |
| CAS consistency | High | Medium |
| Works for Po2? | **No** (MINAO issue) | **To be tested** |

---

## Potential Issues to Watch For

### 1. Inconsistent Virtual Selection Across Geometries

Without virtual mapping, autoCAS might select:
- Virtual 5 on geometry 0
- Virtual 7 on geometry 1 (which is "the same" orbital chemically)

This causes:
- Larger combined CAS (union includes both)
- Different orbital ordering between geometries

**Mitigation**: Use `-u` flag to include all unmappables, or manually verify orbital correspondence in results.

### 2. Core Misclassification

If the -5.0 Ha cutoff doesn't work correctly:
- Some valence orbitals might be marked as core
- Core orbitals might be treated as valence

**Mitigation**: With DKH2 orbitals, this should be fine. Verify by checking the number of core orbitals in Serenity output.

### 3. Large Active Space from Unmappables

If many virtuals are selected but unmapped:
- CAS could become very large
- DMRGSCF cost increases significantly

**Mitigation**: Check CAS size after combination. If too large, use stricter autoCAS thresholds or manually curate.

---

## Conclusion

For Po2 with PM/FB localization:

1. **Virtual localization is disabled** - this is unavoidable
2. **Occupied orbital mapping will work** - PM/FB localize occupied orbitals correctly
3. **Virtual orbitals will be unmapped** - handled via `-u` flag or default exclusion
4. **The workflow should still produce valid results** - autoCAS entropy selection is per-geometry

**Recommended test procedure**:
1. Run PM test with `-u` flag (include unmappables)
2. Run FB test with `-u` flag
3. Compare CAS sizes and selected orbitals
4. If CAS is reasonable, proceed to CASSCF/DMRGSCF

---

## References

- [serenity.py](../../autocas/scine_autocas/interfaces/serenity/serenity.py) - Virtual localization settings
- [GeneralizedDOSTask.h](../../serenity/src/tasks/GeneralizedDOSTask.h) - mapVirtuals documentation
- [cas_combination.py](../../autocas/scine_autocas/cas_selection/cas_combination.py) - CAS combination algorithm
- [protocol.py](../../autocas/scine_autocas/workflows/consistent_active_space/protocol.py) - Unmappable handling
- [IBO_ENERGY_CUTOFF_ANALYSIS.md](./IBO_ENERGY_CUTOFF_ANALYSIS.md) - Energy cutoff details
