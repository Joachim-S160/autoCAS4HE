#!/usr/bin/env python3

import sys
import re
from pathlib import Path
import h5py
import numpy as np
import matplotlib.pyplot as plt

# =========================
# USER SETTINGS
# =========================
CORE_CUTOFF = -5.0  # Hartree
MINAO_PATH = Path("/home/joaschee/autoCAS4HE/serenity/data/basis/MINAO")

# Angular momentum mapping
L_MAP = {
    's': 0,
    'p': 1,
    'd': 2,
    'f': 3,
    'g': 4,
    'h': 5,
    'i': 6
}

# =========================
# MINAO PARSER
# =========================
def count_minimal_basis_for_element(element):
    element = element.lower()
    total_functions = 0
    found = False

    with open(MINAO_PATH, "r") as f:
        lines = f.readlines()

    inside_block = False

    for line in lines:
        line_stripped = line.strip()

        # Detect element start
        if re.match(rf"^{element}\s+MINAO", line_stripped):
            inside_block = True
            found = True
            continue

        # Exit when next element starts
        if inside_block and re.match(r"^[A-Za-z]{1,2}\s+MINAO", line_stripped):
            break

        if inside_block:
            # Detect shell lines like: "11  s"
            m = re.match(r"^\d+\s+([spdfghi])$", line_stripped)
            if m:
                shell = m.group(1)
                l = L_MAP[shell]
                nfunc = 2*l + 1
                total_functions += nfunc

    if not found:
        raise ValueError(f"Element '{element}' not found in MINAO file.")

    return total_functions


# =========================
# MAIN
# =========================
def main():

    if len(sys.argv) not in [3, 4]:
        print("\nUsage:")
        print("Manual mode:")
        print("  python IBO_distr.py file.scf.h5 nMinimalBasisFunctions")
        print("\nAutomatic MINAO mode:")
        print("  python IBO_distr.py file.scf.h5 --element po\n")
        sys.exit(1)

    h5file = sys.argv[1]

    # -------------------------
    # Determine minimal basis (per atom for dimers)
    # -------------------------
    element = None
    if sys.argv[2] == "--element":
        element = sys.argv[3]
        nMinimalBasisFunctions = count_minimal_basis_for_element(element)
        print(f"[INFO] Element: {element.upper()}")
        print(f"[INFO] MINAO per atom: {nMinimalBasisFunctions}")
        print(f"[INFO] MINAO for dimer: {2 * nMinimalBasisFunctions}")
    else:
        # Manual mode: user provides per-atom MINAO count
        nMinimalBasisFunctions = int(sys.argv[2])

    # -------------------------
    # Load data
    # -------------------------
    with h5py.File(h5file, "r") as f:
        mo_energies = f["MO_ENERGIES"][:]
        mo_occ = f["MO_OCCUPATIONS"][:]
        mo_vectors = f["MO_VECTORS"][:]

    nMO = len(mo_energies)
    nBasisFunctions = int(np.sqrt(mo_vectors.size))


    # -------------------------
    # Rydberg count for dimer
    # -------------------------
    nRydberg = nBasisFunctions - 2*nMinimalBasisFunctions
    if nRydberg < 0:
        raise ValueError("nMinimalBasisFunctions > nBasisFunctions → impossible!")

    # Sort by energy
    idx_sorted = np.argsort(mo_energies)
    energies_sorted = mo_energies[idx_sorted]
    occ_sorted = mo_occ[idx_sorted]

    # -------------------------
    # Classification
    # -------------------------
    core_mask = energies_sorted < CORE_CUTOFF

    rydberg_mask = np.zeros(nMO, dtype=bool)
    if nRydberg > 0:
        rydberg_mask[-nRydberg:] = True

    occ_valence_mask = (occ_sorted > 0.0) & (~core_mask)
    virt_valence_mask = (occ_sorted == 0.0) & (~rydberg_mask)

    core_E = energies_sorted[core_mask]
    rydberg_E = energies_sorted[rydberg_mask]
    occ_val_E = energies_sorted[occ_valence_mask]
    virt_val_E = energies_sorted[virt_valence_mask]

    # -------------------------
    # Plot → PDF
    # -------------------------
    plt.figure(figsize=(12, 7))

    bins = 70

    # Colorblind-friendly palette with high contrast
    plt.hist(core_E, bins=bins, color="#8B0000", alpha=0.9, label="Core (dark red)")
    plt.hist(occ_val_E, bins=bins, color="#1f77b4", alpha=0.85, label="Occupied valence (blue)")
    plt.hist(virt_val_E, bins=bins, color="#17becf", alpha=0.85, label="Virtual valence (cyan)")
    plt.hist(rydberg_E, bins=bins, color="#ff7f0e", alpha=0.9, label="Rydberg (orange)")

    plt.axvline(CORE_CUTOFF, color="black", linestyle="--", linewidth=1.5, label=f"Core cutoff ({CORE_CUTOFF} Ha)")

    plt.xlabel("Orbital energy (Hartree)", fontsize=14)
    plt.ylabel("Number of orbitals", fontsize=14)

    # Build title with element info if available
    if element:
        title = f"MO Energy Distribution: {element.upper()}₂ (IBO Classification)"
    else:
        title = "MO Energy Distribution with IBO Classification"
    plt.title(title, fontsize=16)

    plt.legend(frameon=True, fontsize=11, loc='upper right')
    plt.grid(alpha=0.3)
    plt.tight_layout()

    outname = Path(h5file).with_suffix("").name + "_IBO_distribution.pdf"
    plt.savefig(outname)
    plt.close()

    # -------------------------
    # Summary
    # -------------------------
    # Determine total MINAO for the molecule (assumes dimer)
    minao_per_atom = nMinimalBasisFunctions
    total_minao = 2 * minao_per_atom  # Dimer assumption
    if element:
        element_info = f" ({element.upper()}₂ dimer)"
    else:
        element_info = " (dimer)"

    print("\n" + "=" * 50)
    print(f"  Orbital Classification Summary{element_info}")
    print("=" * 50)
    print(f"  Total MOs:                  {nMO}")
    print(f"  Basis functions:            {nBasisFunctions}")
    print(f"  MINAO per atom:             {minao_per_atom}")
    print(f"  Total MINAO (molecule):     {total_minao}")
    print("-" * 50)
    print(f"  Core orbitals:              {len(core_E):4d}  (ε < {CORE_CUTOFF} Ha)")
    print(f"  Occupied valence:           {len(occ_val_E):4d}")
    print(f"  Virtual valence:            {len(virt_val_E):4d}")
    print(f"  Rydberg orbitals:           {len(rydberg_E):4d}  (top {nRydberg} by energy)")
    print("-" * 50)
    print(f"  nOccupied > nMINAO?         {sum(occ_sorted > 0.0) > total_minao}  (IBO issue if True)")
    print("=" * 50)
    print(f"\n[PDF saved as]  {outname}\n")


if __name__ == "__main__":
    main()
