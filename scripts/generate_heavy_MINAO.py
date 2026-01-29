#!/usr/bin/env python3
"""
Generate expanded MINAO basis entries for heavy elements (Z >= 37) from ANO-RCC.

Background
----------
Serenity's MINAO (Minimal Atomic Natural Orbital) basis is used for IAO/IBO
orbital localization (Knizia, JCTC 2013, 9, 4834). For light elements (Z=1-36),
the MINAO contains ALL occupied shells (1s through outermost), derived from
cc-pVTZ. For heavy elements (Z >= 37), the MINAO only has valence shells,
which causes nMINAO < nOcc and crashes the IAO/IBO code.

This script extracts the first N contracted functions per angular momentum
from ANO-RCC, where N = number of occupied shells of that angular momentum.
ANO-RCC is validated by Knizia (Table 1, footnote d of the IAO paper) as
a suitable MINAO source.

The result is a complete MINAO that spans all occupied orbitals, satisfying
the IAO constraint: nMINAO >= nOcc.

Usage
-----
    python3 generate_heavy_MINAO.py

This will:
1. Read ANO-RCC from serenity/data/basis/ANO-RCC
2. Read current MINAO from serenity/data/basis/MINAO
3. Replace/add entries for Z >= 37
4. Write updated MINAO to serenity/data/basis/MINAO
5. Also save a backup at serenity/data/basis/MINAO.bak

Author: autoCAS4HE project
Date: 2026-01-29
"""

import re
import sys
import shutil
from pathlib import Path
from collections import OrderedDict

# ============================================================================
# Configuration
# ============================================================================

SCRIPT_DIR = Path(__file__).parent
PROJECT_DIR = SCRIPT_DIR.parent
MINAO_PATH = PROJECT_DIR / "serenity" / "data" / "basis" / "MINAO"
ANORCC_PATH = PROJECT_DIR / "serenity" / "data" / "basis" / "ANO-RCC"

# Angular momentum labels
L_LABELS = ['s', 'p', 'd', 'f', 'g', 'h', 'i']

# Degeneracy: how many basis functions per contracted function of angular momentum l
L_DEGENERACY = {0: 1, 1: 3, 2: 5, 3: 7, 4: 9, 5: 11, 6: 13}

# ============================================================================
# Electron configuration data
# ============================================================================
#
# For each element Z >= 37, we need the number of OCCUPIED SHELLS per angular
# momentum. This determines how many contracted functions we extract from
# ANO-RCC to form the MINAO.
#
# "Occupied shells" means: how many distinct (n,l) pairs have electrons in
# the ground state or important low-lying states of the atom.
#
# Format: (n_s_shells, n_p_shells, n_d_shells, n_f_shells)
#
# Example for Po (Z=84):
#   Config: [Xe] 4f14 5d10 6s2 6p4
#   s shells: 1s,2s,3s,4s,5s,6s = 6
#   p shells: 2p,3p,4p,5p,6p = 5
#   d shells: 3d,4d,5d = 3
#   f shells: 4f = 1
#   nMINAO/atom = 6 + 5*3 + 3*5 + 1*7 = 43

# Ordered list of element symbols by Z
ELEMENTS = [
    'h', 'he',
    'li', 'be', 'b', 'c', 'n', 'o', 'f', 'ne',
    'na', 'mg', 'al', 'si', 'p', 's', 'cl', 'ar',
    'k', 'ca', 'sc', 'ti', 'v', 'cr', 'mn', 'fe', 'co', 'ni', 'cu', 'zn',
    'ga', 'ge', 'as', 'se', 'br', 'kr',
    'rb', 'sr',
    'y', 'zr', 'nb', 'mo', 'tc', 'ru', 'rh', 'pd', 'ag', 'cd',
    'in', 'sn', 'sb', 'te', 'i', 'xe',
    'cs', 'ba',
    'la', 'ce', 'pr', 'nd', 'pm', 'sm', 'eu', 'gd', 'tb', 'dy', 'ho', 'er', 'tm', 'yb', 'lu',
    'hf', 'ta', 'w', 're', 'os', 'ir', 'pt', 'au', 'hg',
    'tl', 'pb', 'bi', 'po', 'at', 'rn',
    'fr', 'ra',
    'ac', 'th', 'pa', 'u', 'np', 'pu', 'am', 'cm',
]

def get_z(symbol):
    """Get atomic number from element symbol."""
    return ELEMENTS.index(symbol.lower()) + 1


def get_occupied_shells(z):
    """
    Return (n_s, n_p, n_d, n_f) = number of occupied shells per angular
    momentum for element with atomic number z.

    These counts determine how many contracted functions per l to extract
    from ANO-RCC to form the MINAO.

    The counts are based on which (n,l) subshells are occupied in the atom's
    ground state configuration, considering all electrons including core.
    """
    # Period 5, s-block: Rb(37), Sr(38)
    # [Kr] ns^x  =>  s: 1s-5s=5, p: 2p-4p=3, d: 3d=1
    if 37 <= z <= 38:
        return (5, 3, 1, 0)

    # Period 5, d-block: Y(39) - Cd(48)
    # [Kr] 4d^x 5s^y  =>  s:5, p:3, d: 3d,4d=2
    if 39 <= z <= 48:
        return (5, 3, 2, 0)

    # Period 5, p-block: In(49) - Xe(54)
    # [Kr] 4d10 5s2 5p^x  =>  s:5, p: 2p-5p=4, d:2
    if 49 <= z <= 54:
        return (5, 4, 2, 0)

    # Period 6, s-block: Cs(55), Ba(56)
    # [Xe] 6s^x  =>  s: 1s-6s=6, p: 2p-5p=4, d: 3d,4d=2
    if 55 <= z <= 56:
        return (6, 4, 2, 0)

    # Lanthanides: La(57) - Lu(71)
    # [Xe] 4f^x 5d^y 6s2  =>  s:6, p:4, d: 3d,4d,5d=3, f: 4f=1
    if 57 <= z <= 71:
        return (6, 4, 3, 1)

    # Period 6, d-block: Hf(72) - Hg(80)
    # [Xe] 4f14 5d^x 6s^y  =>  s:6, p:4, d:3, f:1
    if 72 <= z <= 80:
        return (6, 4, 3, 1)

    # Period 6, p-block: Tl(81) - Rn(86)
    # [Xe] 4f14 5d10 6s2 6p^x  =>  s:6, p: 2p-6p=5, d:3, f:1
    if 81 <= z <= 86:
        return (6, 5, 3, 1)

    # Period 7, s-block: Fr(87), Ra(88)
    # [Rn] 7s^x  =>  s:7, p:5, d:3, f:1
    if 87 <= z <= 88:
        return (7, 5, 3, 1)

    # Actinides: Ac(89) - Cm(96)
    # [Rn] 5f^x 6d^y 7s2  =>  s:7, p:5, d: 3d-6d=4, f: 4f,5f=2
    if 89 <= z <= 96:
        return (7, 5, 4, 2)

    raise ValueError(f"Element Z={z} not handled")


def compute_minao_size(z):
    """Compute the total number of MINAO basis functions for element Z."""
    n_s, n_p, n_d, n_f = get_occupied_shells(z)
    return n_s * 1 + n_p * 3 + n_d * 5 + n_f * 7


# ============================================================================
# ANO-RCC parser
# ============================================================================

def parse_anorcc(filepath):
    """
    Parse the ANO-RCC basis set file.

    Returns a dict: element_symbol -> list of (l_label, n_primitives, data_lines)
    where data_lines is a list of "exponent  coefficient" strings.

    Each entry in the list is one contracted function. Functions sharing the
    same primitives (same l and same n_primitives appearing consecutively)
    share the same exponents but have different contraction coefficients.
    """
    elements = OrderedDict()

    with open(filepath) as f:
        lines = f.readlines()

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # Match element header: "po ANO-RCC"
        m = re.match(r'^([a-z]{1,2})\s+ANO-RCC', line, re.IGNORECASE)
        if m:
            elem = m.group(1).lower()
            contractions = []
            i += 1  # skip '*' line

            # Now parse contracted functions until next element or $end
            i += 1  # skip the '*'
            while i < len(lines):
                line = lines[i].strip()

                # Check if we hit next element or end
                if re.match(r'^[a-z]{1,2}\s+ANO-RCC', line, re.IGNORECASE):
                    break
                if line.startswith('$'):
                    break
                if line == '*':
                    i += 1
                    break

                # Match contraction header: "25  s" or "22  p"
                cm = re.match(r'^\s*(\d+)\s+([spdfghi])\s*$', line)
                if cm:
                    n_prims = int(cm.group(1))
                    l_label = cm.group(2)
                    data = []
                    for j in range(n_prims):
                        i += 1
                        data.append(lines[i].rstrip('\n'))
                    contractions.append((l_label, n_prims, data))
                i += 1

            elements[elem] = contractions
        else:
            i += 1

    return elements


# ============================================================================
# MINAO parser
# ============================================================================

def parse_minao(filepath):
    """
    Parse the MINAO basis set file.

    Returns:
        header_lines: lines before first element (e.g. '$basis')
        elements: OrderedDict of element_symbol -> list of raw text lines
                  (everything between 'elem  MINAO' and the next '*' or element)
        footer_lines: lines after last element (e.g. '$end')
    """
    with open(filepath) as f:
        all_lines = f.readlines()

    header_lines = []
    elements = OrderedDict()
    footer_lines = []

    i = 0
    # Read header
    while i < len(all_lines):
        line = all_lines[i]
        if re.match(r'^[a-z]{1,2}\s+MINAO', line.strip(), re.IGNORECASE):
            break
        header_lines.append(line)
        i += 1

    # Read element blocks
    while i < len(all_lines):
        line = all_lines[i]
        m = re.match(r'^([a-z]{1,2})\s+MINAO', line.strip(), re.IGNORECASE)
        if m:
            elem = m.group(1).lower()
            block_lines = [line]
            i += 1
            # Read until next element header or $end
            while i < len(all_lines):
                next_line = all_lines[i]
                if re.match(r'^[a-z]{1,2}\s+MINAO', next_line.strip(), re.IGNORECASE):
                    break
                if next_line.strip() == '$end':
                    footer_lines.append(next_line)
                    i += 1
                    break
                block_lines.append(next_line)
                i += 1
            elements[elem] = block_lines
        else:
            if all_lines[i].strip() == '$end':
                footer_lines.append(all_lines[i])
            else:
                footer_lines.append(all_lines[i])
            i += 1

    return header_lines, elements, footer_lines


# ============================================================================
# MINAO generation from ANO-RCC
# ============================================================================

def generate_minao_block(elem_symbol, anorcc_contractions, z):
    """
    Generate a MINAO block for one element from its ANO-RCC contractions.

    We take the first N contracted functions per angular momentum, where
    N is determined by get_occupied_shells(z).

    Parameters
    ----------
    elem_symbol : str
        Element symbol (lowercase)
    anorcc_contractions : list of (l_label, n_primitives, data_lines)
        All contracted functions from ANO-RCC for this element
    z : int
        Atomic number

    Returns
    -------
    lines : list of str
        Lines forming the MINAO block (including header and trailing '*')
    """
    n_s, n_p, n_d, n_f = get_occupied_shells(z)
    needed = {'s': n_s, 'p': n_p, 'd': n_d, 'f': n_f}

    # Count how many of each l are available and take the first N
    taken = {'s': 0, 'p': 0, 'd': 0, 'f': 0}
    selected = []

    for l_label, n_prims, data in anorcc_contractions:
        if l_label not in needed:
            continue
        if taken[l_label] < needed[l_label]:
            selected.append((l_label, n_prims, data))
            taken[l_label] += 1

    # Verify we got what we need
    for l_label in ['s', 'p', 'd', 'f']:
        if taken[l_label] < needed[l_label]:
            available = sum(1 for ll, _, _ in anorcc_contractions if ll == l_label)
            raise ValueError(
                f"Element {elem_symbol} (Z={z}): need {needed[l_label]} {l_label}-type "
                f"contractions but ANO-RCC only has {available}"
            )

    # Format output
    lines = []
    lines.append(f"{elem_symbol}   MINAO\n")
    lines.append("*\n")
    for l_label, n_prims, data in selected:
        lines.append(f"     {n_prims}   {l_label}\n")
        for d in data:
            # Reformat data lines to match MINAO style:
            # MINAO uses right-aligned exponent and coefficient columns
            parts = d.strip().split()
            if len(parts) == 2:
                exp_str = parts[0]
                coef_str = parts[1]
                lines.append(f"         {float(exp_str):18.8f}{float(coef_str):20.8f}\n")
            else:
                lines.append(d + '\n')
    lines.append("*\n")

    return lines


# ============================================================================
# Main
# ============================================================================

def main():
    print("=" * 70)
    print("MINAO Expansion: Generating all-shell MINAO from ANO-RCC")
    print("for heavy elements (Z >= 37)")
    print("=" * 70)

    # Parse input files
    print(f"\nReading ANO-RCC from: {ANORCC_PATH}")
    anorcc = parse_anorcc(ANORCC_PATH)
    print(f"  Found {len(anorcc)} elements in ANO-RCC")

    print(f"\nReading MINAO from: {MINAO_PATH}")
    header, minao_elems, footer = parse_minao(MINAO_PATH)
    print(f"  Found {len(minao_elems)} elements in MINAO")

    # Backup
    backup_path = MINAO_PATH.with_suffix('.bak')
    shutil.copy2(MINAO_PATH, backup_path)
    print(f"\n  Backup saved to: {backup_path}")

    # Statistics
    replaced = []
    added = []
    skipped = []
    errors = []

    # Process all elements Z >= 37 that exist in ANO-RCC
    print("\n" + "-" * 70)
    print(f"{'Element':>8} {'Z':>4} {'Shells (s,p,d,f)':>20} {'nMINAO':>8} {'nMINAO_old':>10} {'Action':>10}")
    print("-" * 70)

    new_minao_elems = OrderedDict()

    # First, keep all light elements (Z <= 36) unchanged
    for elem, block in minao_elems.items():
        try:
            z = get_z(elem)
        except ValueError:
            # Unknown element, keep as-is
            new_minao_elems[elem] = block
            continue

        if z <= 36:
            new_minao_elems[elem] = block
            continue

    # Now process heavy elements
    for elem in ELEMENTS[36:]:  # Z >= 37
        z = get_z(elem)

        if elem not in anorcc:
            skipped.append(elem)
            print(f"{elem:>8} {z:>4} {'N/A':>20} {'N/A':>8} {'N/A':>10} {'SKIP':>10}  (not in ANO-RCC)")
            # Keep old entry if it exists
            if elem in minao_elems:
                new_minao_elems[elem] = minao_elems[elem]
            continue

        try:
            shells = get_occupied_shells(z)
            n_minao_new = compute_minao_size(z)

            # Count old MINAO size if the element existed
            old_size = "N/A"
            if elem in minao_elems:
                # Count contractions in old block
                old_count = 0
                for line in minao_elems[elem]:
                    cm = re.match(r'^\s*\d+\s+([spdfghi])\s*$', line.strip())
                    if cm:
                        l = cm.group(1)
                        l_idx = L_LABELS.index(l)
                        old_count += L_DEGENERACY[l_idx]
                old_size = str(old_count)

            # Generate new block
            new_block = generate_minao_block(elem, anorcc[elem], z)
            new_minao_elems[elem] = new_block

            action = "REPLACE" if elem in minao_elems else "ADD"
            if action == "REPLACE":
                replaced.append(elem)
            else:
                added.append(elem)

            shells_str = f"({shells[0]},{shells[1]},{shells[2]},{shells[3]})"
            print(f"{elem:>8} {z:>4} {shells_str:>20} {n_minao_new:>8} {old_size:>10} {action:>10}")

        except Exception as e:
            errors.append((elem, str(e)))
            print(f"{elem:>8} {z:>4} {'ERROR':>20} {'':>8} {'':>10} {'ERROR':>10}  {e}")
            # Keep old entry if it exists
            if elem in minao_elems:
                new_minao_elems[elem] = minao_elems[elem]

    # Write output
    print("\n" + "=" * 70)
    print("Writing updated MINAO file...")

    with open(MINAO_PATH, 'w') as f:
        # Header
        for line in header:
            f.write(line)

        # Elements
        for elem, block in new_minao_elems.items():
            for line in block:
                f.write(line)

        # Footer
        for line in footer:
            f.write(line)

    print(f"  Written to: {MINAO_PATH}")

    # Summary
    print("\n" + "=" * 70)
    print("Summary:")
    print(f"  Replaced: {len(replaced)} elements ({', '.join(replaced[:10])}{'...' if len(replaced) > 10 else ''})")
    print(f"  Added:    {len(added)} elements ({', '.join(added[:10])}{'...' if len(added) > 10 else ''})")
    print(f"  Skipped:  {len(skipped)} elements ({', '.join(skipped)})")
    print(f"  Errors:   {len(errors)} elements ({', '.join(e[0] for e in errors)})")

    # Verify key elements
    print("\nVerification for target molecules:")
    for elem in ['po', 'bi', 'pb', 'o', 'h']:
        z = get_z(elem)
        if z <= 36:
            print(f"  {elem:>4} (Z={z:>3}): light element, unchanged")
        else:
            size = compute_minao_size(z)
            shells = get_occupied_shells(z)
            print(f"  {elem:>4} (Z={z:>3}): nMINAO = {size}, shells = {shells}")

    # Verify molecules
    print("\nMolecule MINAO totals:")
    molecules = {
        'Po2': ['po', 'po'],
        'Bi2': ['bi', 'bi'],
        'PoPb': ['po', 'pb'],
        'PoBi': ['po', 'bi'],
        'Po(OH)2': ['po', 'o', 'h', 'o', 'h'],
        'Po(OH)4': ['po', 'o', 'h', 'o', 'h', 'o', 'h', 'o', 'h'],
    }
    for mol_name, atoms in molecules.items():
        total_minao = 0
        total_electrons = 0
        for atom in atoms:
            z = get_z(atom)
            if z <= 36:
                # Use existing count from file
                if atom in minao_elems:
                    count = 0
                    for line in minao_elems[atom]:
                        cm = re.match(r'^\s*\d+\s+([spdfghi])\s*$', line.strip())
                        if cm:
                            l = cm.group(1)
                            l_idx = L_LABELS.index(l)
                            count += L_DEGENERACY[l_idx]
                    total_minao += count
                else:
                    total_minao += 1  # H fallback
            else:
                total_minao += compute_minao_size(z)
            total_electrons += z
        n_occ = total_electrons // 2
        n_val_virt = total_minao - n_occ
        status = "OK" if n_val_virt > 0 else "PROBLEM"
        print(f"  {mol_name:>10}: nMINAO={total_minao:>4}, nElec={total_electrons:>4}, "
              f"nOcc={n_occ:>4}, nValVirt={n_val_virt:>4}  [{status}]")


if __name__ == '__main__':
    main()
