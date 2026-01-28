#!/usr/bin/env python3
"""
Element data for homonuclear dimer calculations.
Contains bond lengths and spin multiplicities for elements H-Po.

Bond lengths from experimental data or computational estimates.
Spin multiplicities based on ground state electronic configurations.

NOTE: Some elements don't form stable homonuclear dimers (noble gases, some metals).
These are included with estimated van der Waals distances for completeness.
"""

# Element data: {symbol: (Z, bond_length_angstrom, spin_multiplicity, notes)}
# Spin = 1 (singlet), 2 (doublet), 3 (triplet), etc.
# For elements with MINAO data available in Serenity

DIMER_DATA = {
    # Period 1
    "H":  (1,   0.74, 1, "Stable H2"),
    "He": (2,   2.97, 1, "Van der Waals dimer"),

    # Period 2
    "Li": (3,   2.67, 1, "Stable Li2"),
    "Be": (4,   2.45, 1, "Weakly bound Be2"),
    "B":  (5,   1.59, 3, "B2 triplet ground state"),
    "C":  (6,   1.24, 1, "C2 singlet"),
    "N":  (7,   1.10, 1, "Stable N2"),
    "O":  (8,   1.21, 3, "O2 triplet ground state"),
    "F":  (9,   1.41, 1, "Stable F2"),
    "Ne": (10,  3.09, 1, "Van der Waals dimer"),

    # Period 3
    "Na": (11,  3.08, 1, "Stable Na2"),
    "Mg": (12,  3.89, 1, "Weakly bound Mg2"),
    "Al": (13,  2.70, 3, "Al2 triplet"),
    "Si": (14,  2.25, 3, "Si2 triplet ground state"),
    "P":  (15,  1.89, 1, "Stable P2"),
    "S":  (16,  1.89, 3, "S2 triplet ground state"),
    "Cl": (17,  1.99, 1, "Stable Cl2"),
    "Ar": (18,  3.76, 1, "Van der Waals dimer"),

    # Period 4
    "K":  (19,  3.92, 1, "Stable K2"),
    "Ca": (20,  4.28, 1, "Weakly bound Ca2"),
    "Sc": (21,  2.60, 5, "Sc2 quintet"),
    "Ti": (22,  1.94, 3, "Ti2 triplet"),
    "V":  (23,  1.77, 3, "V2 triplet"),
    "Cr": (24,  1.68, 1, "Cr2 singlet, multiple bond"),
    "Mn": (25,  3.40, 1, "Mn2 antiferromagnetic"),
    "Fe": (26,  2.02, 7, "Fe2 septet"),
    "Co": (27,  2.00, 5, "Co2 quintet"),
    "Ni": (28,  2.20, 3, "Ni2 triplet"),
    "Cu": (29,  2.22, 1, "Cu2 singlet"),
    "Zn": (30,  4.19, 1, "Zn2 weakly bound"),
    "Ga": (31,  2.75, 3, "Ga2 triplet"),
    "Ge": (32,  2.44, 3, "Ge2 triplet"),
    "As": (33,  2.10, 1, "As2 singlet"),
    "Se": (34,  2.17, 3, "Se2 triplet"),
    "Br": (35,  2.28, 1, "Stable Br2"),
    "Kr": (36,  4.01, 1, "Van der Waals dimer"),

    # Period 5 (missing Rb, Sr in MINAO)
    "Y":  (39,  2.85, 5, "Y2 quintet"),
    "Zr": (40,  2.24, 3, "Zr2 triplet"),
    "Nb": (41,  2.08, 3, "Nb2 triplet"),
    "Mo": (42,  1.93, 1, "Mo2 singlet, sextuple bond"),
    "Tc": (43,  2.13, 3, "Tc2 triplet"),
    "Ru": (44,  2.28, 7, "Ru2 septet"),
    "Rh": (45,  2.28, 5, "Rh2 quintet"),
    "Pd": (46,  2.48, 3, "Pd2 triplet"),
    "Ag": (47,  2.53, 1, "Ag2 singlet"),
    "Cd": (48,  4.07, 1, "Cd2 weakly bound"),
    "In": (49,  3.01, 3, "In2 triplet"),
    "Sn": (50,  2.75, 3, "Sn2 triplet"),
    "Sb": (51,  2.34, 1, "Sb2 singlet"),
    "Te": (52,  2.56, 3, "Te2 triplet"),
    "I":  (53,  2.67, 1, "Stable I2"),
    "Xe": (54,  4.36, 1, "Van der Waals dimer"),

    # Period 6 (missing Cs, Ba, La-Lu in MINAO) - 5d and 6p elements
    "Hf": (72,  2.30, 3, "Hf2 triplet"),
    "Ta": (73,  2.15, 3, "Ta2 triplet"),
    "W":  (74,  2.05, 1, "W2 singlet"),
    "Re": (75,  2.24, 3, "Re2 triplet"),
    "Os": (76,  2.30, 7, "Os2 septet"),
    "Ir": (77,  2.27, 5, "Ir2 quintet"),
    "Pt": (78,  2.33, 3, "Pt2 triplet"),
    "Au": (79,  2.47, 1, "Au2 singlet"),
    "Hg": (80,  3.69, 1, "Hg2 weakly bound"),
    "Tl": (81,  3.00, 3, "Tl2 triplet"),
    "Pb": (82,  2.93, 3, "Pb2 triplet"),
    "Bi": (83,  2.66, 1, "Bi2 singlet"),
    "Po": (84,  2.00, 1, "Po2 estimated"),
    "At": (85,  2.85, 1, "At2 estimated"),
    "Rn": (86,  4.50, 1, "Van der Waals dimer"),
}


def get_total_electrons(symbol):
    """Return total electrons for dimer (2 * atomic number)."""
    return 2 * DIMER_DATA[symbol][0]


def is_singlet_ground_state(symbol):
    """Check if the dimer has singlet ground state."""
    return DIMER_DATA[symbol][2] == 1


def get_openmolcas_spin(symbol):
    """
    Return the SPIN keyword value for OpenMolcas.
    OpenMolcas uses SPIN = 2S+1 (multiplicity), e.g., SPIN=1 for singlet.
    """
    return DIMER_DATA[symbol][2]


def get_dimer_bond_length(symbol):
    """Return bond length in Angstrom."""
    return DIMER_DATA[symbol][1]


def generate_xyz(symbol, bond_length=None):
    """Generate XYZ format string for homonuclear dimer."""
    if bond_length is None:
        bond_length = get_dimer_bond_length(symbol)

    half_dist = bond_length / 2.0
    return f"""2
{symbol}2 molecule - {bond_length:.4f} Angstrom bond
{symbol}  {-half_dist:.6f}   0.000000   0.000000
{symbol}   {half_dist:.6f}   0.000000   0.000000
"""


def list_available_elements():
    """Return list of elements available in MINAO (and in our data)."""
    return sorted(DIMER_DATA.keys(), key=lambda x: DIMER_DATA[x][0])


if __name__ == "__main__":
    # Print table of all elements
    print(f"{'Element':<8} {'Z':<4} {'Bond (Å)':<10} {'Spin':<6} {'2*Z':<6} Notes")
    print("-" * 70)
    for el in list_available_elements():
        z, bond, spin, notes = DIMER_DATA[el]
        print(f"{el:<8} {z:<4} {bond:<10.2f} {spin:<6} {2*z:<6} {notes}")
