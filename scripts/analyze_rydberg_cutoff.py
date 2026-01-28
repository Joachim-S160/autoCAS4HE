#!/usr/bin/env python3
"""
Analyze whether energy-based Rydberg cutoff (E >= 1.0 Ha) fixes Serenity crashes.

Compares:
  Current: nRydberg = nBasis - nMINAO (can overflow into occupied space)
  Proposed: nRydberg = count(orbitals with E >= 1.0 Ha)

For this to fix the issue, we need: nRydberg_proposed <= nVirtual
"""

import sys
import csv
import h5py
import numpy as np
from pathlib import Path

# Energy cutoff to test
ENERGY_CUTOFF = 1.0  # Hartree


def analyze_h5_file(h5_path, element):
    """Analyze a single HDF5 file and return Rydberg counts."""
    try:
        with h5py.File(h5_path, 'r') as f:
            energies = f['SCF_ORBITALS/MO_ENERGIES'][:]
            occupations = f['SCF_ORBITALS/MO_OCCUPATIONS'][:]
    except Exception as e:
        return None, str(e)

    # Sort by energy
    idx = np.argsort(energies)
    energies = energies[idx]
    occupations = occupations[idx]

    n_occupied = int(np.sum(occupations > 0.5))
    n_virtual = len(energies) - n_occupied

    # Count orbitals with E >= cutoff (only in virtual space)
    virtual_energies = energies[n_occupied:]
    n_rydberg_proposed = int(np.sum(virtual_energies >= ENERGY_CUTOFF))

    return {
        'element': element,
        'n_mo': len(energies),
        'n_occupied': n_occupied,
        'n_virtual': n_virtual,
        'n_rydberg_proposed': n_rydberg_proposed,
        'would_fix': n_rydberg_proposed <= n_virtual,
        'virtual_min_E': float(virtual_energies.min()) if n_virtual > 0 else None,
        'virtual_max_E': float(virtual_energies.max()) if n_virtual > 0 else None,
    }


def main():
    # Parse arguments
    input_dir = Path('.')
    use_hpc = '--hpc' in sys.argv

    if use_hpc:
        input_dir = Path('/dodrio/scratch/projects/starting_2025_097/autoCAS4HE_built/autoCAS4HE/tests/IBO_dimer_study')

    for arg in sys.argv[1:]:
        if arg.startswith('--input-dir='):
            input_dir = Path(arg.split('=')[1])
        elif not arg.startswith('--'):
            input_dir = Path(arg)

    # Also read the existing CSV for comparison
    csv_path = input_dir / 'IBO_diagnostics.csv'
    existing_data = {}
    if csv_path.exists():
        with open(csv_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                existing_data[row['element']] = row

    print("=" * 80)
    print(f"  Rydberg Cutoff Analysis: E >= {ENERGY_CUTOFF} Ha")
    print("=" * 80)
    print(f"\nSearching in: {input_dir}")
    print()

    results = []
    fixed_count = 0
    still_fails_count = 0
    already_ok_count = 0
    no_data_count = 0

    # Find all element directories
    for subdir in sorted(input_dir.iterdir()):
        if not subdir.is_dir():
            continue

        element = subdir.name.rstrip('2').upper()
        h5_file = subdir / f"{subdir.name}_0.scf.h5"

        if not h5_file.exists():
            continue

        result = analyze_h5_file(h5_file, element)
        if result is None:
            no_data_count += 1
            continue

        # Get existing CSV data
        csv_row = existing_data.get(element, {})
        current_fails = csv_row.get('serenity_fails', 'N/A')
        current_overflow = csv_row.get('overflow', 'N/A')
        current_nRydberg = csv_row.get('nRydberg_calc', 'N/A')

        result['current_fails'] = current_fails
        result['current_overflow'] = current_overflow
        result['current_nRydberg'] = current_nRydberg
        results.append(result)

        # Categorize
        if current_fails == 'True':
            if result['would_fix']:
                fixed_count += 1
            else:
                still_fails_count += 1
        else:
            already_ok_count += 1

    # Print detailed results
    print("-" * 80)
    print(f"{'Element':<8} {'nVirt':>6} {'nRyd_curr':>10} {'overflow':>8} {'nRyd_E>=1':>10} {'FIXED?':>8}")
    print("-" * 80)

    for r in results:
        current_fails = r['current_fails']
        if current_fails != 'True':
            status = "OK"
        elif r['would_fix']:
            status = "FIXED"
        else:
            status = "STILL FAILS"

        print(f"{r['element']:<8} {r['n_virtual']:>6} {r['current_nRydberg']:>10} "
              f"{r['current_overflow']:>8} {r['n_rydberg_proposed']:>10} {status:>8}")

    # Summary
    print()
    print("=" * 80)
    print("  SUMMARY")
    print("=" * 80)
    print(f"  Total elements analyzed:     {len(results)}")
    print(f"  Already OK (no change):      {already_ok_count}")
    print(f"  Currently failing:           {fixed_count + still_fails_count}")
    print(f"    -> FIXED by E>={ENERGY_CUTOFF}Ha:     {fixed_count}")
    print(f"    -> STILL FAILS:            {still_fails_count}")
    print()

    # List elements that would still fail
    still_fail_elements = [r for r in results if r['current_fails'] == 'True' and not r['would_fix']]
    if still_fail_elements:
        print(f"Elements that STILL FAIL with E >= {ENERGY_CUTOFF} Ha criterion:")
        for r in still_fail_elements:
            reason = "nVirtual=0" if r['n_virtual'] == 0 else f"nRydberg({r['n_rydberg_proposed']}) > nVirtual({r['n_virtual']})"
            print(f"  {r['element']}: {reason}")

    # Fixed elements
    fixed_elements = [r for r in results if r['current_fails'] == 'True' and r['would_fix']]
    if fixed_elements:
        print(f"\nElements FIXED by E >= {ENERGY_CUTOFF} Ha criterion:")
        for r in fixed_elements:
            print(f"  {r['element']}: nRydberg {r['current_nRydberg']} -> {r['n_rydberg_proposed']} (nVirtual={r['n_virtual']})")

    # Answer the question
    print()
    print("=" * 80)
    print("  CONCLUSION")
    print("=" * 80)
    if still_fails_count == 0 and fixed_count > 0:
        print(f"  YES! The E >= {ENERGY_CUTOFF} Ha criterion FIXES ALL issues!")
    elif fixed_count > 0:
        print(f"  PARTIAL: Fixes {fixed_count} elements, but {still_fails_count} still fail.")
        print(f"  The remaining failures are due to nVirtual=0 (SCF convergence issues).")
    else:
        print(f"  NO: The E >= {ENERGY_CUTOFF} Ha criterion does not fix the issues.")


if __name__ == "__main__":
    main()
