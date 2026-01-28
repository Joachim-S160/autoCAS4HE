#!/usr/bin/env python3
"""
IBO Distribution Analysis Script

Analyzes orbital energy distributions for IBO localization in Serenity.
Generates dual-panel plots and saves diagnostic data for developing
improved Rydberg classification criteria.
"""

import sys
import re
import csv
import json
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
    nRydberg = max(0, nBasisFunctions - 2*nMinimalBasisFunctions)

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
    # rydberg_actual = min(nRydberg, nVirtual)  # What Serenity SHOULD do
    # rydberg_mask_fixed = np.zeros(nMO, dtype=bool)
    # if rydberg_actual > 0:
    #     rydberg_mask_fixed[-rydberg_actual:] = True
    # rydberg_mask_fixed = rydberg_mask_fixed & (occ_sorted == 0.0)  # Only virtuals

    # Virtual valence: virtual and NOT Rydberg
    virt_valence_mask = (occ_sorted == 0.0) & (~rydberg_mask)

    # For plotting: show ALL orbitals in their Serenity-assigned categories
    # Overlaps will appear as stacked bars (showing the problematic double-counting)
    core_E = energies_sorted[core_occ_mask]           # Core occupied (E < -5 Ha)
    occ_val_E = energies_sorted[occ_valence_mask]     # Occupied valence (includes those also marked Rydberg!)
    virt_val_E = energies_sorted[virt_valence_mask]   # Virtual NOT in Rydberg
    rydberg_E = energies_sorted[rydberg_mask]         # ALL top nRydberg (includes occupied if overflow!)

    # Store overflow info for reporting
    rydberg_overflow = nRydberg - nVirtual if nRydberg > nVirtual else 0
    serenity_fails = rydberg_overflow > 0

    # -------------------------
    # Key energies for analysis
    # -------------------------
    homo_energy = energies_sorted[occ_sorted > 0.0].max() if any(occ_sorted > 0.0) else np.nan
    virtual_energies = energies_sorted[occ_sorted == 0.0]
    lumo_energy = virtual_energies[0] if len(virtual_energies) > 0 else np.nan
    lumo_plus_5 = virtual_energies[4] if len(virtual_energies) > 4 else np.nan
    lumo_plus_10 = virtual_energies[9] if len(virtual_energies) > 9 else np.nan
    rydberg_start = rydberg_E.min() if len(rydberg_E) > 0 else np.nan
    rydberg_end = rydberg_E.max() if len(rydberg_E) > 0 else np.nan
    core_min = core_E.min() if len(core_E) > 0 else np.nan
    core_max = core_E.max() if len(core_E) > 0 else np.nan

    # Total MINAO for molecule (dimer = 2x per atom)
    total_minao = 2 * nMinimalBasisFunctions

    # -------------------------
    # Save diagnostic data to CSV (append mode)
    # -------------------------
    csv_file = Path(h5file).parent / "IBO_diagnostics.csv"
    file_exists = csv_file.exists()

    diag_data = {
        'element': element.upper() if element else 'unknown',
        'nMO': nMO,
        'nBasis': nBasisFunctions,
        'nMINAO_atom': nMinimalBasisFunctions,
        'nMINAO_total': total_minao,
        'nOccupied': nOccupied,
        'nVirtual': nVirtual,
        'nCore': len(core_E),
        'nOccValence': len(occ_val_E),
        'nVirtValence': len(virt_val_E),
        'nRydberg_calc': nRydberg,
        'nRydberg_actual': len(rydberg_E),
        'overflow': rydberg_overflow,
        'serenity_fails': serenity_fails,
        'HOMO': f"{homo_energy:.6f}",
        'LUMO': f"{lumo_energy:.6f}" if not np.isnan(lumo_energy) else 'N/A',
        'LUMO+5': f"{lumo_plus_5:.6f}" if not np.isnan(lumo_plus_5) else 'N/A',
        'LUMO+10': f"{lumo_plus_10:.6f}" if not np.isnan(lumo_plus_10) else 'N/A',
        'Rydberg_start': f"{rydberg_start:.6f}" if not np.isnan(rydberg_start) else 'N/A',
        'Rydberg_end': f"{rydberg_end:.6f}" if not np.isnan(rydberg_end) else 'N/A',
        'Core_min': f"{core_min:.6f}" if not np.isnan(core_min) else 'N/A',
        'Core_max': f"{core_max:.6f}" if not np.isnan(core_max) else 'N/A',
        'HOMO_LUMO_gap': f"{lumo_energy - homo_energy:.6f}" if not np.isnan(lumo_energy) else 'N/A',
    }

    with open(csv_file, 'a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=diag_data.keys())
        if not file_exists:
            writer.writeheader()
        writer.writerow(diag_data)

    print(f"[INFO] Diagnostic data appended to {csv_file}")

    # -------------------------
    # Check for SCF failure (unbound electrons)
    # -------------------------
    scf_failed = homo_energy > 0
    if scf_failed:
        print(f"[WARNING] SCF FAILED: HOMO = {homo_energy:.3f} Ha (positive = unbound electrons)")
        print(f"[WARNING] Skipping plot for {element} - results are unphysical")
        print(f"[WARNING] Try different spin multiplicity or basis set")
        return  # Don't plot unphysical results

    # -------------------------
    # Plot → Dual panel (core zoom on LEFT, valence/Rydberg on RIGHT)
    # -------------------------
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 7), gridspec_kw={'width_ratios': [1, 2]})

    # === LEFT PANEL: Core region zoom ===
    if len(core_E) > 0:
        core_e_min = core_E.min() - 5.0
        core_e_max = CORE_CUTOFF + 2.0

        # Background
        ax1.axvspan(core_e_min, CORE_CUTOFF, alpha=0.15, color="#8B0000", label="_nolegend_")

        # Adaptive binning for core region
        n_core_bins = min(30, max(10, len(core_E) // 3))
        core_bin_edges = np.linspace(core_e_min, core_e_max, n_core_bins)

        ax1.hist(core_E, bins=core_bin_edges, color="#8B0000", alpha=0.9, edgecolor="black", linewidth=1.0,
                rwidth=0.85, label=f"Core: {len(core_E)}")

        ax1.axvline(CORE_CUTOFF, color="black", linestyle="--", linewidth=1.5, label=f"Cutoff ({CORE_CUTOFF} Ha)")
        ax1.set_xlabel("Orbital energy (Hartree)", fontsize=12)
        ax1.set_ylabel("Number of orbitals", fontsize=12)
        ax1.set_xlim(core_e_min, core_e_max)
        ax1.legend(frameon=True, fontsize=9, loc='upper left')
        ax1.grid(alpha=0.3, zorder=0)
        # ax1.set_title(f"Core Region (E < {CORE_CUTOFF} Ha)", fontsize=12)
    else:
        ax1.text(0.5, 0.5, "No core orbitals", ha='center', va='center', fontsize=14, transform=ax1.transAxes)
        ax1.set_title("Core Region", fontsize=12)

    # === RIGHT PANEL: Valence and Rydberg (starting from -6 Ha) ===
    valence_e_min = -6.0  # Start from -6 Ha
    e_max = energies_sorted.max() + 1.0

    # Background colored regions (light hues) - red hue for E < -5 Ha even without core
    ax2.axvspan(valence_e_min, CORE_CUTOFF, alpha=0.15, color="#8B0000", label="_nolegend_")  # Core region hue
    ax2.axvspan(CORE_CUTOFF, homo_energy + 0.1, alpha=0.15, color="#1f77b4", label="_nolegend_")  # Occ valence
    ax2.axvspan(homo_energy + 0.1, rydberg_start - 0.1 if not np.isnan(rydberg_start) else e_max,
                alpha=0.25, color="#9467bd", label="_nolegend_")  # Virt valence
    ax2.axvspan(rydberg_start - 0.1 if not np.isnan(rydberg_start) else e_max, e_max,
                alpha=0.15, color="#ff7f0e", label="_nolegend_")  # Rydberg

    # Use common bin edges for valence/Rydberg range
    bin_edges = np.linspace(valence_e_min, e_max, 50)

    # Histograms with orbital counts in legend (filter to visible range)
    # Core orbitals that fall in this range (unlikely but possible)
    core_in_range = core_E[core_E >= valence_e_min] if len(core_E) > 0 else np.array([])
    if len(core_in_range) > 0:
        ax2.hist(core_in_range, bins=bin_edges, color="#8B0000", alpha=0.9, edgecolor="black", linewidth=1.0,
                rwidth=0.85, label=f"Core: {len(core_E)}")

    ax2.hist(occ_val_E, bins=bin_edges, color="#1f77b4", alpha=1.0, edgecolor="black", linewidth=1.0,
            rwidth=0.85, label=f"Occ. valence: {len(occ_val_E)}")
    ax2.hist(virt_val_E, bins=bin_edges, color="#9467bd", alpha=0.85, edgecolor="black", linewidth=1.0,
            rwidth=0.85, label=f"Virt. valence: {len(virt_val_E)}")
    ax2.hist(rydberg_E, bins=bin_edges, color="#ff7f0e", alpha=0.75, edgecolor="black", linewidth=1.0,
            rwidth=0.85, label=f"Rydberg: {len(rydberg_E)}")

    # Vertical lines for boundaries
    ax2.axvline(CORE_CUTOFF, color="black", linestyle="--", linewidth=1.5, label=f"Core cutoff ({CORE_CUTOFF} Ha)")
    ax2.axvline(homo_energy, color="green", linestyle="-.", linewidth=1.2, label=f"HOMO ({homo_energy:.2f} Ha)")
    if not np.isnan(rydberg_start):
        ax2.axvline(rydberg_start, color="red", linestyle=":", linewidth=1.2, label=f"Rydberg start ({rydberg_start:.2f} Ha)")

    ax2.set_xlabel("Orbital energy (Hartree)", fontsize=12)
    ax2.set_ylabel("Number of orbitals", fontsize=12)
    ax2.set_xlim(valence_e_min, e_max)
    ax2.legend(frameon=True, fontsize=9, loc='upper left')
    ax2.grid(alpha=0.3, zorder=0)
    # ax2.set_title("Valence & Rydberg Region (E ≥ -6 Ha)", fontsize=12)

    # === SERENITY FAILS warning ===
    if serenity_fails:
        # Add prominent red warning text
        fig.text(0.5, 0.95, "SERENITY FAILS", fontsize=24, fontweight='bold',
                 color='red', ha='center', va='top',
                 bbox=dict(boxstyle='round,pad=0.3', facecolor='yellow', edgecolor='red', linewidth=3))
        # Also add details
        fig.text(0.5, 0.89, f"nRydberg ({nRydberg}) > nVirtual ({nVirtual}) → overflow: {rydberg_overflow}",
                 fontsize=11, color='red', ha='center', va='top')

    # === Main title ===
    if element:
        main_title = f"MO Energy Distribution: {element.upper()}₂ — MINAO: {total_minao} ({nMinimalBasisFunctions}/atom)"
    else:
        main_title = f"MO Energy Distribution — MINAO: {total_minao}"

    fig.suptitle(main_title, fontsize=14, fontweight='bold', y=0.99 if not serenity_fails else 0.85)

    plt.tight_layout()
    if serenity_fails:
        plt.subplots_adjust(top=0.82)
    else:
        plt.subplots_adjust(top=0.92)

    # Save as both PDF and PNG (PNG for GIF creation)
    base_name = Path(h5file).with_suffix("").name + "_IBO_distribution"
    pdf_name = base_name + ".pdf"
    png_name = base_name + ".png"

    plt.savefig(pdf_name, dpi=150)
    plt.savefig(png_name, dpi=150)
    plt.close()

    # -------------------------
    # Summary
    # -------------------------
    minao_per_atom = nMinimalBasisFunctions
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
    print("  KEY ENERGIES (for Rydberg cutoff development):")
    print(f"    HOMO:                     {homo_energy:10.4f} Ha")
    print(f"    LUMO:                     {lumo_energy:10.4f} Ha" if not np.isnan(lumo_energy) else "    LUMO:                     N/A")
    print(f"    LUMO+5:                   {lumo_plus_5:10.4f} Ha" if not np.isnan(lumo_plus_5) else "    LUMO+5:                   N/A")
    print(f"    LUMO+10:                  {lumo_plus_10:10.4f} Ha" if not np.isnan(lumo_plus_10) else "    LUMO+10:                  N/A")
    print(f"    Rydberg start:            {rydberg_start:10.4f} Ha" if not np.isnan(rydberg_start) else "    Rydberg start:            N/A")
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
    print(f"\n[PDF saved as]  {pdf_name}")
    print(f"[PNG saved as]  {png_name}\n")


if __name__ == "__main__":
    main()
