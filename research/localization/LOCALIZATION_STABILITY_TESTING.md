# Localization Stability Testing Plan

**Goal**: Validate that IBO localization produces stable, transferable results for heavy element systems once relativistic orbitals are available.

---

## Tests to Perform

### 1. Geometry Distortion Stability

Test whether localized orbitals remain consistent under small geometry perturbations:

```
For Po2 at bond lengths: 2.8, 2.9, 3.0, 3.1, 3.2 Å
  - Run IBO localization at each geometry
  - Compare: Do the same chemical orbitals (σ, σ*, lone pairs) appear?
  - Check: Is the orbital character preserved or do orbitals "switch" identity?
```

**Why this matters**: The consistent active space protocol maps orbitals across geometries. If IBO gives inconsistent orbital characters, the mapping will fail.

### 2. Localization Method Comparison

Even though IBO is preferred, compare against other methods for validation:

| Method | Test | Expected Outcome |
|--------|------|------------------|
| IBO | Po2 at multiple geometries | Consistent σ/σ*/LP character |
| Pipek-Mezey | Same geometries | Compare orbital shapes |
| Foster-Boys | Same geometries | Compare orbital shapes |

**Note**: We prefer IBO because it's physically motivated (IAO projection), not population-based like PM or spatial-extent-based like Foster-Boys. See [IBO_VS_OTHER_LOCALIZATION.md](IBO_VS_OTHER_LOCALIZATION.md).

### 3. Basis Set Sensitivity

Test whether localized orbitals are stable across basis set sizes:
- ANO-RCC-VDZP (current)
- ANO-RCC-VTZP
- ANO-RCC-VQZP

IBO should be more basis-set independent than PM due to the MINAO reference basis.

### 4. Relativistic Effects on Localization

Once we have relativistic orbitals (via OpenMolcas), compare:
- IBO of non-relativistic orbitals (if it doesn't crash)
- IBO of DKH2-relativistic orbitals

**Key question**: Do the localized orbitals have the same chemical character, or does the relativistic treatment change the bonding picture?

---

## Success Criteria

A localization method is suitable for autoCAS4HE if:

1. **Consistency**: Same orbital character across small geometry distortions
2. **Mappability**: DOS orbital mapping succeeds across all geometries
3. **Numerical Stability**: No crashes or convergence failures

---

## Test Implementation

### Script Structure

```bash
tests/
├── localization_stability/
│   ├── geometries/
│   │   ├── Po2_2.8A.xyz
│   │   ├── Po2_2.9A.xyz
│   │   ├── Po2_3.0A.xyz
│   │   ├── Po2_3.1A.xyz
│   │   └── Po2_3.2A.xyz
│   ├── run_stability_test.py
│   └── analyze_orbital_consistency.py
```

### Metrics to Collect

1. **Orbital overlap** between geometries (should be > 0.9 for same orbital)
2. **Orbital character** (σ, σ*, π, lone pair) - manual or automatic classification
3. **Mapping success rate** - does DOS mapping find all correspondences?
4. **Localization convergence** - number of iterations, final gradient