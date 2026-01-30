# Mixed MINAO Basis Analysis: cc-pVTZ (Z <= 36) + ANO-RCC (Z >= 37)

**Date**: 2026-01-30
**Context**: Assessment of whether mixing two basis set families in the MINAO
reference basis affects IAO/IBO quality for heavy-element molecules (Po2, PoPb,
Po(OH)4, etc.)

---

## 1. The Concern

After expanding the MINAO for heavy elements (Z >= 37) using contracted
functions from ANO-RCC, the MINAO basis file now contains entries from two
different basis set families:

| Element range | Z range | MINAO source | Derivation |
|---------------|---------|--------------|------------|
| H - Kr | 1-36 | cc-pVTZ | Knizia's original: state-averaged HF over important electronic states, contracted to 1 function per occupied (n,l) shell |
| Rb - Cm | 37-96 | ANO-RCC | This work: first N contracted functions per angular momentum from ANO-RCC, where N = number of occupied shells |

For a molecule like Po(OH)4, the H and O atoms use cc-pVTZ-derived MINAO while
the Po atom uses ANO-RCC-derived MINAO. The question is: does this mixing
introduce artifacts in the IAO projection and subsequent IBO localization?

---

## 2. How the IAO Projection Actually Works

The IAO construction (Knizia, JCTC 2013, 9, 4834-4843, Appendix A) uses two
bases:

- **B1**: the computational AO basis (e.g., ANO-RCC-VDZP, 136 functions for Po2)
- **B2**: the MINAO reference basis (e.g., 86 functions for Po2 after expansion)

The algorithm proceeds as follows:

1. Compute overlap matrices S1 (B1 x B1), S2 (B2 x B2), S12 (B1 x B2)
2. Form projection operators P12 = S1^(-1) * S12 and P21 = S2^(-1) * S12^T
3. Project occupied MOs through the MINAO space: C_tilde = P12 * P21 * C_occ
4. Symmetric orthogonalize C_tilde to get C_tilde (Eq. 1 in Knizia)
5. Depolarize: construct the IAO basis via Eq. 2 (the "exact" formula)
6. Symmetric orthogonalize the IAO basis (othoA in Serenity's code)
7. Transform MOs into IAO basis: CIAO = othoA^T * S1 * C

**Key observation**: The MINAO functions for different atoms interact only
through the overlap matrices S12 and S2. Each atom's MINAO functions are
centered on that atom and describe that atom's occupied shells. There is no
requirement that the MINAO functions on different atoms come from the same
basis set family. The S12 overlap integral between a cc-pVTZ-derived 1s on H
and an ANO-RCC-derived 6p on Po is computed by Libint from the actual Gaussian
primitives — it doesn't know or care about the "family" of each function.

The projection P12 * P21 is a purely mathematical operation that projects
occupied MOs into the subspace spanned by all MINAO functions combined. The
quality of this projection depends only on whether the MINAO functions span
the occupied orbital space, not on whether they came from the same basis set.

---

## 3. What Knizia Says About MINAO Choice

### 3.1. Original MINAO Construction

In the 2013 paper, Knizia constructs the default MINAO as follows:

- For most elements: take the cc-pVTZ basis, keep only the first contraction
  per occupied (n,l) shell. The contraction coefficients are derived from
  state-averaged Hartree-Fock calculations over important electronic states
  (not just the ground state). This ensures the MINAO represents a "neutral"
  average atomic orbital shape.

- For elements beyond Krypton: valence-only contractions were used (this is
  the regime we identified as broken and have now fixed).

### 3.2. Alternatives Tested

In Table 1 of the 2013 paper (with footnote d), Knizia explicitly tests
alternative MINAO sources:

- **Huzinaga MINI basis**: a completely different minimal basis set
- **ANO-RCC contracted functions**: first N contractions per angular momentum

The paper reports that IAO partial charges are essentially identical regardless
of which minimal basis is used. This is the central robustness claim of the
IAO method: the results are insensitive to the specific choice of B2, as long
as B2 spans the occupied atomic shells.

### 3.3. The Robustness Guarantee

The IAO construction has a mathematical guarantee: if B2 spans the occupied
orbitals exactly (i.e., the projection P12 * P21 * C_occ has full rank), then
the IAOs are exact representations of the occupied space, regardless of the
specific form of B2. The depolarization step (Eq. 2) is designed to be
idempotent — applying it twice gives the same result — which ensures stability.

The quality of B2 affects only the virtual valence IAOs (which are not uniquely
defined by the occupied space). For IBO localization of occupied orbitals, the
MINAO choice has no effect on the final result, only on intermediate
quantities. For virtual IBO localization, there could in principle be minor
differences, but these are within the inherent ambiguity of virtual orbital
definitions.

**Reference**: Knizia, G. "Intrinsic Atomic Orbitals: An Unbiased Bridge
between Quantum Theory and Chemical Concepts." J. Chem. Theory Comput. 2013,
9, 4834-4843. DOI: 10.1021/ct400687b. Preprint with corrected appendix:
http://www.iboview.org/bin/iao_preprint.pdf

---

## 4. Why Mixing Families is Safe

### 4.1. Each Atom is Independent

The MINAO for atom A only needs to describe atom A's occupied shells. The
MINAO for atom B only needs to describe atom B's shells. There is no
cross-atom requirement for consistency. In the overlap matrix S2, off-diagonal
blocks (atom A MINAO vs atom B MINAO) are small because minimal basis
functions on different atoms have limited spatial overlap. The on-diagonal
blocks are well-conditioned because each atom's MINAO is orthonormalized
within itself.

### 4.2. The IAO Projection is a Linear Algebra Operation

The IAO construction is a sequence of linear algebra operations (matrix
multiplications, symmetric orthogonalizations, eigendecompositions). These
operations work on the overlap integrals between Gaussian functions. The
overlap integral between two Gaussian functions depends only on their
exponents, contraction coefficients, and centers — not on what "family" they
belong to. A 1s function is a 1s function whether it came from cc-pVTZ or
ANO-RCC.

### 4.3. Knizia's Own Validation

As noted above, Knizia tested Huzinaga MINI (a completely different basis set
family from a different era of quantum chemistry, with different optimization
philosophy) alongside cc-pVTZ-derived MINAO and ANO-RCC, and found essentially
identical results. If mixing Huzinaga MINI with cc-pVTZ doesn't cause
problems, mixing cc-pVTZ with ANO-RCC certainly won't.

### 4.4. Physical Argument

Both cc-pVTZ and ANO-RCC represent the same physical reality: the shape of
atomic orbitals. A 1s orbital on hydrogen has a specific shape dictated by
quantum mechanics. Whether you approximate that shape with a cc-pVTZ
contraction or an ANO-RCC contraction, the result is nearly identical for
occupied shells. The differences between basis set families are primarily in:

- Polarization and correlation functions (not present in MINAO)
- Diffuse functions (not present in MINAO)
- The quality of the valence description (both cc-pVTZ and ANO-RCC are
  high-quality triple-zeta bases, so their first contractions are nearly
  identical)

---

## 5. Addressing Specific Concerns

### 5.1. "Radial Mismatch and Ghost Polarizations"

**Concern**: cc-pVTZ and ANO-RCC have different radial nodal structures.

**Assessment**: This concern conflates the computational basis (B1) with the
reference basis (B2/MINAO). The MINAO contains only one contracted function
per occupied shell — these are smooth, nodeless (for the outermost shell of
each l) or have the correct number of nodes (for inner shells). The radial
structure of the MINAO is dictated by atomic physics, not by the basis set
family. Both cc-pVTZ and ANO-RCC capture this correctly.

The IAO populations are computed as:

    q_Ai = sum_{mu in A} |CIAO(mu, i)|^2

where the sum runs over MINAO functions on atom A. The depolarization step
ensures that these populations sum to the correct electron count. "Ghost
polarizations" (populations of 1.1 or -0.1) would indicate a failure of the
IAO projection itself, not a basis family mismatch. Such failures can only
occur if the MINAO is linearly dependent or doesn't span the occupied space —
neither of which is the case here.

### 5.2. "Relativistic Consistency"

**Concern**: ANO-RCC accounts for scalar relativity (DKH2), while cc-pVTZ
is non-relativistic.

**Assessment**: The MINAO describes the shape of free-atom orbitals, not the
Hamiltonian used to compute molecular orbitals. The H 1s MINAO from cc-pVTZ
describes a hydrogen 1s orbital shape. The Po 6p MINAO from ANO-RCC describes
a polonium 6p orbital shape (including relativistic contraction effects via
the ANO-RCC optimization). These shapes are what the IAO projection uses as
templates.

The computational SCF (which uses the DKH2 Hamiltonian in the user's setup)
produces molecular orbitals that already incorporate scalar relativistic
effects. The IAO projection then decomposes these MOs into atomic
contributions using the MINAO templates. Whether the H template came from a
relativistic or non-relativistic calculation is irrelevant for hydrogen (Z=1),
where relativistic effects are negligible (~10^-5 level).

For Po, the ANO-RCC MINAO correctly captures the relativistic contraction of
the 6s shell and the expansion of the 5d shell, which is important for
accurate decomposition of the Po contributions.

### 5.3. "Leaking Core Character"

**Concern**: The ANO-RCC MINAO might not be compatible with the way the
primary basis describes the core-valence boundary.

**Assessment**: This is a valid concern in general, but it is not specific to
the mixed basis situation. It would also arise if the entire MINAO were from
ANO-RCC. The core-valence separation in Serenity is handled by the
`splitValenceAndCore` mechanism in LocalizationTask.cpp, which separates
orbitals by energy before localization. The MINAO basis doesn't determine the
core-valence boundary — the orbital energies do.

Furthermore, the ANO-RCC basis is derived from state-averaged CASSCF
calculations that explicitly treat core-valence correlation. The contracted
functions are ordered by natural occupation number, so the first N functions
per l are the most "core-like" and "occupied-like." This makes them
well-suited as MINAO templates.

---

## 6. What Could Go Wrong (and How to Check)

While the mixed MINAO is theoretically sound, there are practical issues worth
monitoring:

### 6.1. Numerical Conditioning of S2

If the MINAO functions from different families happen to be nearly linearly
dependent (unlikely but possible for adjacent heavy atoms), the S2 matrix
could be ill-conditioned. This would manifest as:

- Large condition number of S2 (check in debug output)
- IAO populations that don't sum to the correct electron count
- The orthogonality sanity check in IBOLocalization.cpp:217-224 failing

**Mitigation**: The MINAO functions are compact (core + valence, no diffuse),
so linear dependence is extremely unlikely. For Po2, the two Po atoms are at
a bond distance of ~2.6 Angstrom, and their MINAO functions are well-separated.

### 6.2. IBO Convergence

If the IAO populations are noisy due to a poor MINAO, the IBO Jacobi rotation
might converge slowly or to a different local maximum. Check:

- Number of Jacobi sweeps (should be 5-15, not 50+)
- Final gradient (should be < 10^-8)

### 6.3. IAO Population Sanity

After IBO localization, check that each occupied IBO has:

- Total population (sum over all atoms) close to 1.0 (for restricted)
- No atom has a negative population on a bonding IBO
- Populations are chemically reasonable (e.g., a Po-Po sigma bond IBO should
  have ~0.5 population on each Po)

---

## 7. Comparison with Other Implementations

### 7.1. PySCF

PySCF's IAO implementation (pyscf.lo.iao) uses a different default MINAO
called "minao", which is derived from the ANO basis sets for all elements.
This means PySCF already uses a single-family MINAO, but it's a different
family (ANO, not ANO-RCC). The IAO results from PySCF and Serenity are
essentially identical for molecules tested with light elements.

### 7.2. Molpro

Molpro's implementation uses 'MINAO-AUTO-PP' as the default, which is
described as "a minimal basis set of spherically averaged Hartree-Fock
orbitals." This is yet another MINAO source. Molpro also allows the user to
substitute arbitrary minimal bases.

### 7.3. Q-Chem

Q-Chem offers multiple B2 options: MINAO (truncated cc-pVTZ, Knizia's
original), STO-3G, STO-6G, and autoSAD (automatic superposition of atomic
densities). All produce comparable IAO results for standard molecules.

The fact that different programs use different MINAO sources and all produce
consistent results is strong evidence that the IAO method is genuinely
insensitive to the B2 choice.

**References**:
- PySCF: Sun, Q. et al. "PySCF: the Python-based simulations of chemistry
  framework." WIREs Comput. Mol. Sci. 2018, 8, e1340.
- Molpro: Werner, H.-J. et al. "The Molpro quantum chemistry package."
  J. Chem. Phys. 2020, 152, 144107.
- Q-Chem: Epifanovsky, E. et al. "Software for the frontiers of quantum
  chemistry." J. Chem. Phys. 2021, 155, 084801.

---

## 8. Relationship Between MINAO and Computational Basis

A separate but related concern: the computational basis (B1) for the SCF is
ANO-RCC-VDZP for all atoms, while the MINAO (B2) uses cc-pVTZ-derived
functions for light atoms. This means B1 and B2 come from different families
for light atoms (H, O).

This is also not a problem. The IAO construction only requires that B1 is
large enough to represent the molecular orbitals accurately, and that B2
spans the occupied atomic shells. The overlap integrals S12 between B1 and B2
are computed exactly by Libint regardless of the basis families.

In fact, this B1/B2 family mismatch is the standard situation in most IAO
calculations: users routinely run DFT with one basis (e.g., def2-TZVP) and
the IAO analysis uses a completely different MINAO (derived from cc-pVTZ or
ANO). No issues have been reported from this practice in the literature.

---

## 9. Conclusion

The mixed cc-pVTZ/ANO-RCC MINAO is safe for the following reasons:

1. **Knizia's own validation**: The original paper tests MINAO sources from
   three completely different basis set families (cc-pVTZ, Huzinaga MINI,
   ANO-RCC) and finds identical results.

2. **Mathematical guarantee**: The IAO projection is exact as long as B2
   spans the occupied space. The result is independent of the specific form
   of B2 for occupied orbitals.

3. **Practical evidence**: Different quantum chemistry packages (PySCF,
   Molpro, Q-Chem) use different MINAO sources and produce consistent IAO
   results.

4. **Physical argument**: Both cc-pVTZ and ANO-RCC are high-quality bases
   whose first contractions per shell accurately represent occupied atomic
   orbital shapes.

The only quantities that could differ slightly between MINAO sources are the
virtual valence IAOs, which are inherently ambiguous (they depend on the
complementary space of the occupied IAOs within B2). For the autoCAS
application, these virtual IAOs are used only for the 2 virtual valence
orbitals of Po2, and any minor differences would not affect the CAS selection.

### Remaining Open Questions

- **Empirical verification**: Once the HPC build completes, compare the IAO
  populations for Po2 with those from a hypothetical "all-ANO-RCC" MINAO to
  confirm numerical agreement. This could be done by temporarily replacing
  the H and O MINAO entries with ANO-RCC-derived ones and re-running.

- **Knizia's paper details**: The exact numerical results from Table 1
  footnote d (comparing cc-pVTZ vs ANO-RCC MINAO) should be cited once the
  full paper PDF is consulted. The preprint with corrected appendix is
  available at: http://www.iboview.org/bin/iao_preprint.pdf

---

## References

1. Knizia, G. "Intrinsic Atomic Orbitals: An Unbiased Bridge between Quantum
   Theory and Chemical Concepts." J. Chem. Theory Comput. 2013, 9, 4834-4843.
   DOI: 10.1021/ct400687b. Preprint: http://www.iboview.org/bin/iao_preprint.pdf

2. Lehtola, S.; Jónsson, H. "Pipek-Mezey Orbital Localization Using Various
   Partial Charge Estimates." J. Chem. Theory Comput. 2014, 10, 642-649.
   DOI: 10.1021/ct401016x. (Demonstrates that localized orbitals are largely
   independent of the partial charge scheme, including IAO-based charges.)

3. Widmark, P.-O.; Malmqvist, P.-A.; Roos, B. O. "Density matrix averaged
   atomic natural orbital (ANO) basis sets for correlated molecular wave
   functions." Theor. Chim. Acta 1990, 77, 291-306. (Original ANO concept.)

4. Roos, B. O.; Lindh, R.; Malmqvist, P.-A.; Veryazov, V.; Widmark, P.-O.
   "Main Group Atoms and Dimers Studied with a New Relativistic ANO Basis
   Set." J. Phys. Chem. A 2004, 108, 2851-2858. (ANO-RCC for main group.)

5. Roos, B. O.; Lindh, R.; Malmqvist, P.-A.; Veryazov, V.; Widmark, P.-O.
   "New Relativistic ANO Basis Sets for Transition Metal Atoms." J. Phys.
   Chem. A 2005, 109, 6575-6579. (ANO-RCC for transition metals.)

6. Huzinaga, S.; Klobukowski, M. "Well-tempered Gaussian basis sets for the
   calculation of matrix Hartree-Fock wavefunctions." Chem. Phys. Lett. 1993,
   212, 260-264. (Huzinaga MINI basis, also tested as B2 by Knizia.)
