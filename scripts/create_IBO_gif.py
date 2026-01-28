#!/usr/bin/env python3
"""
Create animated GIF and MP4 from IBO distribution plots.

Collects all PNG files from dimer analysis and creates animations
sorted by atomic number (Z) for easy review of trends across the periodic table.

Usage:
    python create_IBO_gif.py [--input-dir DIR] [--output FILE] [--duration MS] [--hpc]

Options:
    --input-dir DIR   Directory containing element subdirectories (default: current dir)
    --output FILE     Output filename base (default: IBO_all_elements)
    --duration MS     Duration per frame in milliseconds (default: 500)
    --hpc             Use HPC paths
"""

import sys
import subprocess
from pathlib import Path
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


def create_mp4_with_ffmpeg(png_files, output_path, duration_ms, input_dir):
    """Create MP4 using ffmpeg with a file list."""
    fps = 1000 / duration_ms  # Convert ms per frame to fps

    # Create a temporary file list for ffmpeg
    list_file = input_dir / '_ffmpeg_input.txt'
    with open(list_file, 'w') as f:
        for z, name, path in png_files:
            # ffmpeg concat demuxer format
            f.write(f"file '{path.absolute()}'\n")
            f.write(f"duration {duration_ms / 1000}\n")
        # Add last frame again (ffmpeg quirk)
        if png_files:
            f.write(f"file '{png_files[-1][2].absolute()}'\n")

    try:
        cmd = [
            'ffmpeg', '-y',  # Overwrite output
            '-f', 'concat',
            '-safe', '0',
            '-i', str(list_file),
            '-vf', 'fps=2,format=yuv420p',  # 2 fps, compatible pixel format
            '-c:v', 'libx264',
            '-preset', 'medium',
            '-crf', '23',
            str(output_path)
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            return True
        else:
            print(f"ffmpeg error: {result.stderr}")
            return False
    except FileNotFoundError:
        return False
    finally:
        if list_file.exists():
            list_file.unlink()


def create_mp4_with_imageio(png_files, output_path, duration_ms):
    """Create MP4 using imageio-ffmpeg."""
    try:
        import imageio.v3 as iio
        fps = 1000 / duration_ms

        # Read all images
        frames = []
        for z, name, path in png_files:
            img = iio.imread(path)
            frames.append(img)

        # Write as MP4
        iio.imwrite(str(output_path), frames, fps=fps, codec='libx264')
        return True
    except ImportError:
        # Try legacy imageio API
        try:
            import imageio
            fps = 1000 / duration_ms

            writer = imageio.get_writer(str(output_path), fps=fps, codec='libx264',
                                        pixelformat='yuv420p', quality=8)
            for z, name, path in png_files:
                img = imageio.imread(path)
                writer.append_data(img)
            writer.close()
            return True
        except Exception as e:
            print(f"imageio error: {e}")
            return False
    except Exception as e:
        print(f"imageio error: {e}")
        return False


def main():
    # Parse arguments
    input_dir = Path('.')
    output_base = 'IBO_all_elements'
    duration = 500  # ms per frame
    use_hpc = '--hpc' in sys.argv

    args = [a for a in sys.argv[1:] if a != '--hpc']
    i = 0
    while i < len(args):
        if args[i] == '--input-dir' and i + 1 < len(args):
            input_dir = Path(args[i + 1])
            i += 2
        elif args[i] == '--output' and i + 1 < len(args):
            output_base = args[i + 1].replace('.gif', '').replace('.mp4', '')
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

    # Sort by atomic number (chemical size)
    png_files.sort(key=lambda x: x[0])

    print(f"Found {len(png_files)} PNG files")
    print("Order (by atomic number Z):")
    for z, name, path in png_files:
        print(f"  Z={z:3d}: {name}")

    # === Create GIF ===
    gif_path = input_dir / f"{output_base}.gif"
    gif_created = False

    try:
        from PIL import Image
        print(f"\nCreating GIF with {duration}ms per frame...")

        images = []
        for z, name, path in png_files:
            img = Image.open(path)
            if img.mode != 'RGB':
                img = img.convert('RGB')
            images.append(img)

        images[0].save(
            gif_path,
            save_all=True,
            append_images=images[1:],
            duration=duration,
            loop=0
        )
        gif_created = True
        print(f"GIF saved to: {gif_path}")
    except ImportError:
        print("\nWARNING: PIL/Pillow not installed, skipping GIF creation.")
        print("Install with: pip install Pillow")

    # === Create MP4 (better for pausing in VSCode) ===
    mp4_path = input_dir / f"{output_base}.mp4"
    mp4_created = False

    print(f"\nCreating MP4 with {duration}ms per frame...")

    # Try imageio first (often available as HPC module)
    try:
        mp4_created = create_mp4_with_imageio(png_files, mp4_path, duration)
    except Exception as e:
        print(f"imageio attempt failed: {e}")

    # Fall back to ffmpeg
    if not mp4_created:
        mp4_created = create_mp4_with_ffmpeg(png_files, mp4_path, duration, input_dir)

    if mp4_created:
        print(f"MP4 saved to: {mp4_path}")
    else:
        print("WARNING: Could not create MP4.")
        print("  Install ffmpeg: apt install ffmpeg / conda install ffmpeg")
        print("  Or install imageio: pip install imageio imageio-ffmpeg")

    # Summary
    print("\n" + "=" * 60)
    print("  Animation Summary")
    print("=" * 60)
    print(f"  Frames: {len(png_files)}")
    print(f"  Duration per frame: {duration}ms")
    print(f"  Total duration: {len(png_files) * duration / 1000:.1f}s")
    if gif_created:
        print(f"  GIF: {gif_path}")
    if mp4_created:
        print(f"  MP4: {mp4_path} (recommended for VSCode)")

    # Show failed elements summary
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
            for elem, overflow in sorted(failed, key=lambda x: ELEMENT_Z.get(x[0].capitalize(), 999)):
                z = ELEMENT_Z.get(elem.capitalize(), '?')
                print(f"  {elem:3s} (Z={z:3}): overflow = {overflow}")
        else:
            print("\nNo elements found that would crash Serenity.")
    else:
        print(f"\nDiagnostics CSV not found at {csv_file}")
        print("Run analyze_all.sh first to generate diagnostic data.")


if __name__ == "__main__":
    main()
