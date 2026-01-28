#!/usr/bin/env python3
"""
Create animated GIF from IBO distribution plots.

Collects all PNG files from dimer analysis and creates an animated GIF
sorted by atomic number (Z) for easy review of trends across the periodic table.

Usage:
    python create_IBO_gif.py [--input-dir DIR] [--output FILE] [--duration MS] [--hpc]

Options:
    --input-dir DIR   Directory containing element subdirectories (default: current dir)
    --output FILE     Output GIF filename (default: IBO_all_elements.gif)
    --duration MS     Duration per frame in milliseconds (default: 500)
    --hpc             Use HPC paths
"""

import sys
from pathlib import Path
import glob
import re

# Element data with atomic numbers for sorting
ELEMENT_Z = {
    'H': 1, 'He': 2, 'Li': 3, 'Be': 4, 'B': 5, 'C': 6, 'N': 7, 'O': 8, 'F': 9, 'Ne': 10,
    'Na': 11, 'Mg': 12, 'Al': 13, 'Si': 14, 'P': 15, 'S': 16, 'Cl': 17, 'Ar': 18, 'K': 19, 'Ca': 20,
    'Sc': 21, 'Ti': 22, 'V': 23, 'Cr': 24, 'Mn': 25, 'Fe': 26, 'Co': 27, 'Ni': 28, 'Cu': 29, 'Zn': 30,
    'Ga': 31, 'Ge': 32, 'As': 33, 'Se': 34, 'Br': 35, 'Kr': 36, 'Rb': 37, 'Sr': 38, 'Y': 39, 'Zr': 40,
    'Nb': 41, 'Mo': 42, 'Tc': 43, 'Ru': 44, 'Rh': 45, 'Pd': 46, 'Ag': 47, 'Cd': 48, 'In': 49, 'Sn': 50,
    'Sb': 51, 'Te': 52, 'I': 53, 'Xe': 54, 'Cs': 55, 'Ba': 56, 'La': 57, 'Ce': 58, 'Pr': 59, 'Nd': 60,
    'Pm': 61, 'Sm': 62, 'Eu': 63, 'Gd': 64, 'Tb': 65, 'Dy': 66, 'Ho': 67, 'Er': 68, 'Tm': 69, 'Yb': 70,
    'Lu': 71, 'Hf': 72, 'Ta': 73, 'W': 74, 'Re': 75, 'Os': 76, 'Ir': 77, 'Pt': 78, 'Au': 79, 'Hg': 80,
    'Tl': 81, 'Pb': 82, 'Bi': 83, 'Po': 84, 'At': 85, 'Rn': 86,
}


def get_atomic_number(element_dir):
    """Extract element symbol from directory name and return atomic number."""
    # Directory names like 'po2', 'n2', 'fe2' etc.
    match = re.match(r'^([a-z]{1,2})2$', element_dir.lower())
    if match:
        symbol = match.group(1).capitalize()
        return ELEMENT_Z.get(symbol, 999)
    return 999


def main():
    # Parse arguments
    input_dir = Path('.')
    output_file = 'IBO_all_elements.gif'
    duration = 500  # ms per frame
    use_hpc = '--hpc' in sys.argv

    args = [a for a in sys.argv[1:] if a != '--hpc']
    i = 0
    while i < len(args):
        if args[i] == '--input-dir' and i + 1 < len(args):
            input_dir = Path(args[i + 1])
            i += 2
        elif args[i] == '--output' and i + 1 < len(args):
            output_file = args[i + 1]
            i += 2
        elif args[i] == '--duration' and i + 1 < len(args):
            duration = int(args[i + 1])
            i += 2
        elif args[i] in ['-h', '--help']:
            print(__doc__)
            sys.exit(0)
        else:
            i += 1

    # Set default input directory for HPC
    if use_hpc and input_dir == Path('.'):
        input_dir = Path('/dodrio/scratch/projects/starting_2025_097/autoCAS4HE_built/autoCAS4HE/tests/IBO_dimer_study')

    print(f"Searching for PNG files in: {input_dir}")

    # Find all PNG files
    png_files = []
    for subdir in input_dir.iterdir():
        if subdir.is_dir():
            for png in subdir.glob('*_IBO_distribution.png'):
                z = get_atomic_number(subdir.name)
                png_files.append((z, subdir.name, png))

    if not png_files:
        print("No PNG files found!")
        print("Make sure IBO_distr.py has been run on the .scf.h5 files first.")
        sys.exit(1)

    # Sort by atomic number
    png_files.sort(key=lambda x: x[0])

    print(f"Found {len(png_files)} PNG files")
    print("Order (by Z):")
    for z, name, path in png_files:
        print(f"  Z={z:3d}: {name}")

    # Try to import PIL
    try:
        from PIL import Image
    except ImportError:
        print("\nERROR: PIL/Pillow not installed.")
        print("Install with: pip install Pillow")
        print("\nAlternatively, use ImageMagick from command line:")
        print(f"  convert -delay {duration // 10} -loop 0 \\")
        for _, _, path in png_files:
            print(f"    {path} \\")
        print(f"    {output_file}")
        sys.exit(1)

    # Create GIF
    print(f"\nCreating GIF with {duration}ms per frame...")

    images = []
    for z, name, path in png_files:
        img = Image.open(path)
        # Convert to RGB if necessary (for GIF compatibility)
        if img.mode != 'RGB':
            img = img.convert('RGB')
        images.append(img)

    # Save as GIF
    output_path = input_dir / output_file
    images[0].save(
        output_path,
        save_all=True,
        append_images=images[1:],
        duration=duration,
        loop=0  # 0 = infinite loop
    )

    print(f"\nGIF saved to: {output_path}")
    print(f"  - {len(images)} frames")
    print(f"  - {duration}ms per frame")
    print(f"  - Total duration: {len(images) * duration / 1000:.1f}s")

    # Also create a summary of failed elements
    print("\n" + "=" * 60)
    print("  Summary: Elements where SERENITY FAILS")
    print("=" * 60)

    csv_file = input_dir / 'IBO_diagnostics.csv'
    if csv_file.exists():
        import csv
        with open(csv_file, 'r') as f:
            reader = csv.DictReader(f)
            failed = []
            for row in reader:
                if row.get('serenity_fails', '').lower() == 'true':
                    failed.append((row['element'], int(row['overflow'])))

        if failed:
            print(f"\n{len(failed)} elements will cause Serenity to crash:\n")
            for elem, overflow in sorted(failed, key=lambda x: ELEMENT_Z.get(x[0], 999)):
                z = ELEMENT_Z.get(elem, '?')
                print(f"  {elem:3s} (Z={z:3}): overflow = {overflow}")
        else:
            print("\nNo elements found that would crash Serenity.")
    else:
        print(f"\nDiagnostics CSV not found at {csv_file}")
        print("Run analyze_all.sh first to generate diagnostic data.")


if __name__ == "__main__":
    main()
