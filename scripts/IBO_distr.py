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

# Paths for different environments
MINAO_PATH_LOCAL = Path("/home/joaschee/autoCAS4HE/serenity/data/basis/MINAO")
MINAO_PATH_HPC = Path("/dodrio/scratch/projects/starting_2025_097/autoCAS4HE_built/autoCAS4HE/serenity/data/basis/MINAO")

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
def count_minimal_basis_for_element(element, minao_path):
    element = element.lower()
    total_functions = 0
    found = False

    with open(minao_path, "r") as f:
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
    # Check for --hpc flag anywhere in arguments
    use_hpc = "--hpc" in sys.argv
    if use_hpc:
        sys.argv.remove("--hpc")

    if len(sys.argv) not in [3, 4]:
        print("\nUsage:")
        print("Manual mode:")
        print("  python IBO_distr.py file.scf.h5 nMinimalBasisFunctions [--hpc]")
        print("\nAutomatic MINAO mode:")
        print("  python IBO_distr.py file.scf.h5 --element po [--hpc]")
        print("\nOptions:")
        print("  --hpc    Use HPC cluster paths (default: local paths)\n")
        sys.exit(1)

    h5file = sys.argv[1]

    # Select MINAO path based on environment
    minao_path = MINAO_PATH_HPC if use_hpc else MINAO_PATH_LOCAL
    if use_hpc:
        print("[INFO] Using HPC paths")

    # -------------------------
    # Determine minimal basis (per atom for dimers)
    # -------------------------
    element = None
    if sys.argv[2] == "--element":
        element = sys.argv[3]
        nMinimalBasisFunctions = count_minimal_basis_for_element(element, minao_path)
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
    # Classification (mimics Serenity's IBO logic)
    # -------------------------
    nOccupied = int((occ_sorted > 0.0).sum())
    nVirtual = nMO - nOccupied

    # Step 1: Core classification (energy-based, applies to ALL orbitals)
    core_mask = energies_sorted < CORE_CUTOFF

    # Step 2: Rydberg classification (top nRydberg by energy)
    # Serenity marks these from highest energy down
    rydberg_mask = np.zeros(nMO, dtype=bool)
    if nRydberg > 0:
        rydberg_mask[-nRydberg:] = True

    # CRITICAL: Check for overlap (Serenity would crash here!)
    overlap_mask = core_mask & rydberg_mask
    n_overlap = overlap_mask.sum()

    # Occupied orbitals marked as Rydberg (would cause crash)
    occ_as_rydberg = (occ_sorted > 0.0) & rydberg_mask
    n_occ_as_rydberg = occ_as_rydberg.sum()

    # Serenity-accurate classification (mutually exclusive)
    # Core: occupied with E < cutoff (flag=1 in Serenity)
    core_occ_mask = (occ_sorted > 0.0) & core_mask

    # Valence occupied: occupied and NOT core
    occ_valence_mask = (occ_sorted > 0.0) & (~core_mask)

    # Rydberg: virtual AND in top nRydberg (but Serenity caps at nVirtual)
    rydberg_actual = min(nRydberg, nVirtual)  # What Serenity SHOULD do
    rydberg_mask_fixed = np.zeros(nMO, dtype=bool)
    if rydberg_actual > 0:
        rydberg_mask_fixed[-rydberg_actual:] = True
    rydberg_mask_fixed = rydberg_mask_fixed & (occ_sorted == 0.0)  # Only virtuals

    # Virtual valence: virtual and NOT Rydberg
    virt_valence_mask = (occ_sorted == 0.0) & (~rydberg_mask_fixed)

    core_E = energies_sorted[core_occ_mask]
    rydberg_E = energies_sorted[rydberg_mask_fixed]
    occ_val_E = energies_sorted[occ_valence_mask]
    virt_val_E = energies_sorted[virt_valence_mask]

    # Store overflow info for reporting
    rydberg_overflow = nRydberg - nVirtual if nRydberg > nVirtual else 0

    # -------------------------
    # Plot → PDF
    # -------------------------
    fig, ax = plt.subplots(figsize=(12, 7))

    # Determine key energy boundaries
    homo_energy = energies_sorted[occ_sorted > 0.0].max() if any(occ_sorted > 0.0) else 0.0
    lumo_energy = energies_sorted[occ_sorted == 0.0].min() if any(occ_sorted == 0.0) else 0.0
    rydberg_start = rydberg_E.min() if len(rydberg_E) > 0 else energies_sorted.max()

    # Plot range
    e_min = energies_sorted.min() - 1.0
    e_max = energies_sorted.max() + 1.0

    # Background colored regions (light hues) - plot first so they're behind bars
    ax.axvspan(e_min, CORE_CUTOFF, alpha=0.15, color="#8B0000", label="_nolegend_")  # Core region (light red)
    ax.axvspan(CORE_CUTOFF, homo_energy + 0.1, alpha=0.15, color="#1f77b4", label="_nolegend_")  # Occ valence (light blue)
    ax.axvspan(homo_energy + 0.1, rydberg_start - 0.1, alpha=0.15, color="#9467bd", label="_nolegend_")  # Virt valence (light purple)
    ax.axvspan(rydberg_start - 0.1, e_max, alpha=0.15, color="#ff7f0e", label="_nolegend_")  # Rydberg (light orange)

    # Use common bin edges across full energy range for consistent bar widths
    bin_edges = np.linspace(e_min, e_max, 40)

    # Total MINAO for molecule (dimer = 2x per atom)
    total_minao = 2 * nMinimalBasisFunctions

    # Colorblind-friendly palette with high contrast and visible edges
    # Include orbital counts in legend labels
    ax.hist(core_E, bins=bin_edges, color="#8B0000", alpha=0.9, edgecolor="black", linewidth=1.2,
            rwidth=0.85, label=f"Core: {len(core_E)}")
    ax.hist(occ_val_E, bins=bin_edges, color="#1f77b4", alpha=0.85, edgecolor="black", linewidth=1.2,
            rwidth=0.85, label=f"Occ. valence: {len(occ_val_E)}")
    ax.hist(virt_val_E, bins=bin_edges, color="#9467bd", alpha=0.85, edgecolor="black", linewidth=1.2,
            rwidth=0.85, label=f"Virt. valence: {len(virt_val_E)}")
    ax.hist(rydberg_E, bins=bin_edges, color="#ff7f0e", alpha=0.9, edgecolor="black", linewidth=1.2,
            rwidth=0.85, label=f"Rydberg: {len(rydberg_E)}")

    # Vertical lines for boundaries
    ax.axvline(CORE_CUTOFF, color="black", linestyle="--", linewidth=1.5, label=f"Core cutoff ({CORE_CUTOFF} Ha)")
    ax.axvline(homo_energy, color="green", linestyle="-.", linewidth=1.2, label=f"HOMO ({homo_energy:.2f} Ha)")
    ax.axvline(rydberg_start, color="red", linestyle=":", linewidth=1.2, label=f"Rydberg start ({rydberg_start:.2f} Ha)")

    ax.set_xlabel("Orbital energy (Hartree)", fontsize=14)
    ax.set_ylabel("Number of orbitals", fontsize=14)
    ax.set_xlim(e_min, e_max)

    # Build title with element info and MINAO count
    if element:
        title = f"MO Energy Distribution: {element.upper()}₂ — MINAO: {total_minao} ({nMinimalBasisFunctions}/atom)"
    else:
        title = f"MO Energy Distribution — MINAO: {total_minao}"
    ax.set_title(title, fontsize=16)

    ax.legend(frameon=True, fontsize=10, loc='upper left')
    ax.grid(alpha=0.3, zorder=0)
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

    print("\n" + "=" * 60)
    print(f"  Orbital Classification Summary{element_info}")
    print("=" * 60)
    print(f"  Total MOs:                  {nMO}")
    print(f"  Basis functions:            {nBasisFunctions}")
    print(f"  MINAO per atom:             {minao_per_atom}")
    print(f"  Total MINAO (molecule):     {total_minao}")
    print("-" * 60)
    print(f"  Occupied orbitals:          {nOccupied:4d}")
    print(f"  Virtual orbitals:           {nVirtual:4d}")
    print("-" * 60)
    print(f"  Core (occupied, ε<{CORE_CUTOFF}):   {len(core_E):4d}")
    print(f"  Occupied valence:           {len(occ_val_E):4d}")
    print(f"  Virtual valence:            {len(virt_val_E):4d}")
    print(f"  Rydberg (shown):            {len(rydberg_E):4d}")
    print("-" * 60)
    print("  SERENITY IBO ANALYSIS:")
    print(f"    nRydberg calculated:      {nRydberg:4d}  (nBasis - nMINAO)")
    print(f"    nVirtual available:       {nVirtual:4d}")
    if rydberg_overflow > 0:
        print(f"    !! OVERFLOW:              {rydberg_overflow:4d}  orbitals into occupied space")
        print(f"    !! Core-Rydberg overlap:  {n_overlap:4d}  (would crash Serenity)")
        print(f"    !! Occ marked as Rydberg: {n_occ_as_rydberg:4d}")
        print("-" * 60)
        print("  STATUS: IBO WILL CRASH - nRydberg > nVirtual")
    else:
        print(f"    Overflow:                 None")
        print("-" * 60)
        print("  STATUS: IBO should work")
    print("=" * 60)
    print(f"\n[PDF saved as]  {outname}\n")


if __name__ == "__main__":
    main()
