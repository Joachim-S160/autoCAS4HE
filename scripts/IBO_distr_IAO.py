#!/usr/bin/env python3
"""
IBO Distribution Analysis Script - IAO Constrained Version

Analyzes orbital energy distributions for IBO localization showing the
proper IAO constraint: nValVirt = nMINAO - nOcc

This is the physically correct classification when nMINAO >= nOcc is satisfied.

Usage:
    python IBO_distr_IAO.py file.scf.h5 [--hpc]

The element is auto-detected from the filename (e.g., po2_0.scf.h5 -> Po)
"""

import sys
import re
from pathlib import Path
import h5py
import numpy as np
import matplotlib.pyplot as plt

# =========================
# CONSTANTS
# =========================
CORE_CUTOFF = -5.0  # Hartree

# Angular momentum mapping
L_MAP = {'s': 0, 'p': 1, 'd': 2, 'f': 3, 'g': 4, 'h': 5, 'i': 6}

# Paths for different environments
MINAO_PATH_LOCAL = Path("/home/joaschee/autoCAS4HE/serenity/data/basis/MINAO")
MINAO_PATH_HPC = Path("/dodrio/scratch/projects/starting_2025_097/autoCAS4HE_built/autoCAS4HE/serenity/data/basis/MINAO")


def auto_detect_element(h5file: str) -> str:
    """
    Auto-detect element from HDF5 filename.

    Examples:
        po2_0.scf.h5 -> po
        system_0.scf.h5 -> None (will need manual input)
        n2_eq.scf.h5 -> n
    """
    filename = Path(h5file).stem.lower()  # e.g., "po2_0.scf" -> "po2_0"

    # Common patterns: element2_*, element_*, elementN_*
    # Try to match element symbol at start
    patterns = [
        r'^([a-z]{1,2})2[_\d]',  # po2_0, n2_1, etc.
        r'^([a-z]{1,2})[_\d]',    # po_0, n_1, etc.
        r'^([a-z]{1,2})\d',       # po2, n2, etc.
    ]

    for pattern in patterns:
        match = re.match(pattern, filename)
        if match:
            elem = match.group(1)
            # Validate it's a real element (basic check)
            if elem.capitalize() in ELEMENT_Z:
                return elem

    return None


# Atomic numbers
ELEMENT_Z = {
    'H': 1, 'He': 2, 'Li': 3, 'Be': 4, 'B': 5, 'C': 6, 'N': 7, 'O': 8,
    'F': 9, 'Ne': 10, 'Na': 11, 'Mg': 12, 'Al': 13, 'Si': 14, 'P': 15,
    'S': 16, 'Cl': 17, 'Ar': 18, 'K': 19, 'Ca': 20, 'Sc': 21, 'Ti': 22,
    'V': 23, 'Cr': 24, 'Mn': 25, 'Fe': 26, 'Co': 27, 'Ni': 28, 'Cu': 29,
    'Zn': 30, 'Ga': 31, 'Ge': 32, 'As': 33, 'Se': 34, 'Br': 35, 'Kr': 36,
    'Rb': 37, 'Sr': 38, 'Y': 39, 'Zr': 40, 'Nb': 41, 'Mo': 42, 'Tc': 43,
    'Ru': 44, 'Rh': 45, 'Pd': 46, 'Ag': 47, 'Cd': 48, 'In': 49, 'Sn': 50,
    'Sb': 51, 'Te': 52, 'I': 53, 'Xe': 54, 'Cs': 55, 'Ba': 56, 'La': 57,
    'Hf': 72, 'Ta': 73, 'W': 74, 'Re': 75, 'Os': 76, 'Ir': 77, 'Pt': 78,
    'Au': 79, 'Hg': 80, 'Tl': 81, 'Pb': 82, 'Bi': 83, 'Po': 84, 'At': 85,
    'Rn': 86,
}


def count_minimal_basis_for_element(element: str, minao_path: Path) -> int:
    """Count MINAO basis functions for an element from the MINAO file."""
    element = element.lower()
    total_functions = 0
    found = False

    with open(minao_path, "r") as f:
        lines = f.readlines()

    inside_block = False

    for line in lines:
        line_stripped = line.strip()

        # Detect element start
        if re.match(rf"^{element}\s+MINAO", line_stripped, re.IGNORECASE):
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
                nfunc = 2 * l + 1
                total_functions += nfunc

    if not found:
        raise ValueError(f"Element '{element}' not found in MINAO file: {minao_path}")

    return total_functions


def main():
    # Check for --hpc flag
    use_hpc = "--hpc" in sys.argv
    if use_hpc:
        sys.argv.remove("--hpc")

    # Check for --element flag
    element_override = None
    if "--element" in sys.argv:
        idx = sys.argv.index("--element")
        if idx + 1 < len(sys.argv):
            element_override = sys.argv[idx + 1]
            sys.argv.pop(idx + 1)
            sys.argv.pop(idx)

    if len(sys.argv) < 2:
        print("\nUsage:")
        print("  python IBO_distr_IAO.py file.scf.h5 [--element ELEM] [--hpc]")
        print("\nElement is auto-detected from filename (e.g., po2_0.scf.h5 -> Po)")
        print("Or specify manually with --element")
        print("\nOptions:")
        print("  --element ELEM  Specify element symbol (e.g., po, n, c)")
        print("  --hpc           Use HPC cluster paths for MINAO file\n")
        sys.exit(1)

    h5file = sys.argv[1]

    # Select MINAO path
    minao_path = MINAO_PATH_HPC if use_hpc else MINAO_PATH_LOCAL
    if use_hpc:
        print("[INFO] Using HPC paths")

    # Get element (override or auto-detect)
    if element_override:
        element = element_override.lower()
        print(f"[INFO] Using specified element: {element.upper()}")
    else:
        element = auto_detect_element(h5file)
        if element is None:
            print(f"[ERROR] Could not auto-detect element from filename: {h5file}")
            print("        Expected format: element2_N.scf.h5 (e.g., po2_0.scf.h5)")
            print("        Use --element ELEM to specify manually")
            sys.exit(1)
        print(f"[INFO] Auto-detected element: {element.upper()}")

    # Get MINAO count
    nMinimalBasisFunctions = count_minimal_basis_for_element(element, minao_path)
    print(f"[INFO] MINAO per atom: {nMinimalBasisFunctions}")

    # For dimer
    nMINAO = 2 * nMinimalBasisFunctions
    print(f"[INFO] MINAO for dimer: {nMINAO}")

    # -------------------------
    # Load data from HDF5
    # -------------------------
    with h5py.File(h5file, "r") as f:
        mo_energies = f["MO_ENERGIES"][:]
        mo_occ = f["MO_OCCUPATIONS"][:]
        mo_vectors = f["MO_VECTORS"][:]

    nMO = len(mo_energies)
    nBasisFunctions = int(np.sqrt(mo_vectors.size))

    # Sort by energy
    idx_sorted = np.argsort(mo_energies)
    energies_sorted = mo_energies[idx_sorted]
    occ_sorted = mo_occ[idx_sorted]

    # -------------------------
    # Basic counts
    # -------------------------
    nOccupied = int((occ_sorted > 0.0).sum())
    nVirtual = nMO - nOccupied

    # -------------------------
    # IAO Constraint Classification
    # -------------------------
    # The key constraint: nMINAO >= nOcc
    # Virtual valence = nMINAO - nOcc
    # Rydberg = nVirtual - nValVirt

    iao_satisfied = nMINAO >= nOccupied
    if iao_satisfied:
        nValVirt_IAO = nMINAO - nOccupied
        nRydberg_IAO = nVirtual - nValVirt_IAO
    else:
        nValVirt_IAO = 0
        nRydberg_IAO = nVirtual
        print(f"[WARNING] IAO constraint violated: nMINAO ({nMINAO}) < nOcc ({nOccupied})")

    # -------------------------
    # Serenity's approach (for comparison)
    # nRydberg = nBasis - nMINAO
    # -------------------------
    nRydberg_Serenity = max(0, nBasisFunctions - nMINAO)
    serenity_overflow = nRydberg_Serenity > nVirtual

    # -------------------------
    # Energy-based classification for plotting
    # -------------------------
    # Core: E < -5 Ha (occupied only)
    core_mask = (occ_sorted > 0.0) & (energies_sorted < CORE_CUTOFF)
    # Occupied valence: occupied and E >= -5 Ha
    occ_valence_mask = (occ_sorted > 0.0) & (energies_sorted >= CORE_CUTOFF)

    # IAO-constrained virtual classification
    # Virtual valence: lowest nValVirt_IAO virtual orbitals by energy
    # Rydberg: remaining virtuals
    virtual_indices = np.where(occ_sorted == 0.0)[0]
    virtual_energies = energies_sorted[virtual_indices]

    # Sort virtuals by energy (they should already be sorted, but be safe)
    virt_sort_idx = np.argsort(virtual_energies)

    virt_valence_IAO_mask = np.zeros(nMO, dtype=bool)
    rydberg_IAO_mask = np.zeros(nMO, dtype=bool)

    for i, idx in enumerate(virt_sort_idx):
        global_idx = virtual_indices[idx]
        if i < nValVirt_IAO:
            virt_valence_IAO_mask[global_idx] = True
        else:
            rydberg_IAO_mask[global_idx] = True

    # Extract energies for each category
    core_E = energies_sorted[core_mask]
    occ_val_E = energies_sorted[occ_valence_mask]
    virt_val_IAO_E = energies_sorted[virt_valence_IAO_mask]
    rydberg_IAO_E = energies_sorted[rydberg_IAO_mask]

    # Key energies
    homo_energy = energies_sorted[occ_sorted > 0.0].max() if any(occ_sorted > 0.0) else np.nan
    virtual_energies_all = energies_sorted[occ_sorted == 0.0]
    lumo_energy = virtual_energies_all[0] if len(virtual_energies_all) > 0 else np.nan

    # -------------------------
    # Check for SCF failure
    # -------------------------
    if homo_energy > 0:
        print(f"[WARNING] SCF FAILED: HOMO = {homo_energy:.3f} Ha (positive = unbound electrons)")
        print(f"[WARNING] Skipping plot - results are unphysical")
        return

    # -------------------------
    # PLOT: IAO-Constrained Classification
    # -------------------------
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 7), gridspec_kw={'width_ratios': [1, 2]})

    # === LEFT PANEL: Core region zoom ===
    if len(core_E) > 0:
        core_e_min = core_E.min() - 5.0
        core_e_max = CORE_CUTOFF + 2.0

        ax1.axvspan(core_e_min, CORE_CUTOFF, alpha=0.15, color="#8B0000", label="_nolegend_")

        n_core_bins = min(30, max(10, len(core_E) // 3))
        core_bin_edges = np.linspace(core_e_min, core_e_max, n_core_bins)

        ax1.hist(core_E, bins=core_bin_edges, color="#8B0000", alpha=0.9, edgecolor="black",
                 linewidth=1.0, rwidth=0.85, label=f"Core: {len(core_E)}")

        ax1.axvline(CORE_CUTOFF, color="black", linestyle="--", linewidth=1.5,
                    label=f"Cutoff ({CORE_CUTOFF} Ha)")
        ax1.set_xlabel("Orbital energy (Hartree)", fontsize=12)
        ax1.set_ylabel("Number of orbitals", fontsize=12)
        ax1.set_xlim(core_e_min, core_e_max)
        ax1.legend(frameon=True, fontsize=9, loc='upper left')
        ax1.grid(alpha=0.3, zorder=0)
    else:
        ax1.text(0.5, 0.5, "No core orbitals", ha='center', va='center', fontsize=14,
                 transform=ax1.transAxes)
        ax1.set_title("Core Region", fontsize=12)

    # === RIGHT PANEL: Valence and Rydberg ===
    valence_e_min = -6.0
    e_max = energies_sorted.max() + 1.0

    # Background colors
    ax2.axvspan(valence_e_min, CORE_CUTOFF, alpha=0.15, color="#8B0000", label="_nolegend_")
    ax2.axvspan(CORE_CUTOFF, homo_energy + 0.1, alpha=0.15, color="#1f77b4", label="_nolegend_")

    # Virtual valence region (between HOMO and first Rydberg)
    if len(virt_val_IAO_E) > 0 and len(rydberg_IAO_E) > 0:
        vv_max = virt_val_IAO_E.max()
        ryd_min = rydberg_IAO_E.min()
        ax2.axvspan(homo_energy + 0.1, (vv_max + ryd_min) / 2, alpha=0.25, color="#9467bd", label="_nolegend_")
        ax2.axvspan((vv_max + ryd_min) / 2, e_max, alpha=0.15, color="#ff7f0e", label="_nolegend_")
    elif len(rydberg_IAO_E) > 0:
        ax2.axvspan(homo_energy + 0.1, e_max, alpha=0.15, color="#ff7f0e", label="_nolegend_")

    bin_edges = np.linspace(valence_e_min, e_max, 50)

    # Histograms
    core_in_range = core_E[core_E >= valence_e_min] if len(core_E) > 0 else np.array([])
    if len(core_in_range) > 0:
        ax2.hist(core_in_range, bins=bin_edges, color="#8B0000", alpha=0.9, edgecolor="black",
                 linewidth=1.0, rwidth=0.85, label=f"Core: {len(core_E)}")

    ax2.hist(occ_val_E, bins=bin_edges, color="#1f77b4", alpha=1.0, edgecolor="black",
             linewidth=1.0, rwidth=0.85, label=f"Occ. valence: {len(occ_val_E)}")
    ax2.hist(virt_val_IAO_E, bins=bin_edges, color="#9467bd", alpha=0.85, edgecolor="black",
             linewidth=1.0, rwidth=0.85, label=f"Virt. valence: {len(virt_val_IAO_E)}")
    ax2.hist(rydberg_IAO_E, bins=bin_edges, color="#ff7f0e", alpha=0.75, edgecolor="black",
             linewidth=1.0, rwidth=0.85, label=f"Rydberg: {len(rydberg_IAO_E)}")

    # Vertical lines
    ax2.axvline(CORE_CUTOFF, color="black", linestyle="--", linewidth=1.5,
                label=f"Core cutoff ({CORE_CUTOFF} Ha)")
    ax2.axvline(homo_energy, color="green", linestyle="-.", linewidth=1.2,
                label=f"HOMO ({homo_energy:.2f} Ha)")
    if len(virt_val_IAO_E) > 0 and len(rydberg_IAO_E) > 0:
        boundary = (virt_val_IAO_E.max() + rydberg_IAO_E.min()) / 2
        ax2.axvline(boundary, color="red", linestyle=":", linewidth=2.0,
                    label=f"IAO boundary ({boundary:.2f} Ha)")

    ax2.set_xlabel("Orbital energy (Hartree)", fontsize=12)
    ax2.set_ylabel("Number of orbitals", fontsize=12)
    ax2.set_xlim(valence_e_min, e_max)
    ax2.legend(frameon=True, fontsize=9, loc='upper left')
    ax2.grid(alpha=0.3, zorder=0)

    # === Title and constraint info ===
    constraint_status = "SATISFIED" if iao_satisfied else "VIOLATED"
    constraint_color = "darkgreen" if iao_satisfied else "red"

    main_title = f"IBO Classification: {element.upper()}₂ — IAO Constraint"
    fig.suptitle(main_title, fontsize=14, fontweight='bold', y=0.98)

    # Add constraint box
    constraint_text = (
        f"IAO Constraint: nMINAO ≥ nOcc\n"
        f"nMINAO = {nMINAO}  |  nOcc = {nOccupied}\n"
        f"nValVirt = nMINAO - nOcc = {nValVirt_IAO}\n"
        f"nRydberg = nVirt - nValVirt = {nRydberg_IAO}"
    )
    fig.text(0.5, 0.91, constraint_text, fontsize=11, ha='center', va='top',
             fontfamily='monospace',
             bbox=dict(boxstyle='round,pad=0.4', facecolor='lightgreen' if iao_satisfied else 'lightyellow',
                       edgecolor=constraint_color, linewidth=2))

    plt.tight_layout()
    plt.subplots_adjust(top=0.82)

    # Save
    base_name = Path(h5file).with_suffix("").name + "_IBO_IAO"
    pdf_name = base_name + ".pdf"
    png_name = base_name + ".png"

    plt.savefig(pdf_name, dpi=150)
    plt.savefig(png_name, dpi=150)
    plt.close()

    # -------------------------
    # Summary
    # -------------------------
    print("\n" + "=" * 65)
    print(f"  IBO Classification Summary: {element.upper()}₂ (IAO Constrained)")
    print("=" * 65)
    print(f"  Total MOs:              {nMO}")
    print(f"  Basis functions:        {nBasisFunctions}")
    print(f"  MINAO per atom:         {nMinimalBasisFunctions}")
    print(f"  MINAO (molecule):       {nMINAO}")
    print("-" * 65)
    print(f"  Occupied orbitals:      {nOccupied:4d}")
    print(f"  Virtual orbitals:       {nVirtual:4d}")
    print("-" * 65)
    print(f"  IAO CONSTRAINT: nMINAO >= nOcc")
    print(f"    nMINAO:               {nMINAO:4d}")
    print(f"    nOcc:                 {nOccupied:4d}")
    print(f"    Status:               {constraint_status}")
    print("-" * 65)
    print(f"  CLASSIFICATION (IAO-constrained):")
    print(f"    Core (E < {CORE_CUTOFF} Ha):    {len(core_E):4d}")
    print(f"    Occ. valence:         {len(occ_val_E):4d}")
    print(f"    Virt. valence:        {nValVirt_IAO:4d}  (= nMINAO - nOcc)")
    print(f"    Rydberg:              {nRydberg_IAO:4d}  (= nVirt - nValVirt)")
    print("-" * 65)
    print(f"  SERENITY COMPARISON (nRydberg = nBasis - nMINAO):")
    print(f"    nRydberg (Serenity):  {nRydberg_Serenity:4d}")
    print(f"    Overflow:             {'YES - would crash!' if serenity_overflow else 'No'}")
    print("=" * 65)
    print(f"\n[Saved] {png_name}")
    print(f"[Saved] {pdf_name}\n")


if __name__ == "__main__":
    main()
