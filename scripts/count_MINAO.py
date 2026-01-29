import sys
import re
from pathlib import Path

# Fixed MINAO path
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


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python script.py <element>")
        print("Example: python script.py po")
        sys.exit(1)

    element = sys.argv[1]

    try:
        n = count_minimal_basis_for_element(element)
        print(f"Element: {element}")
        print(f"Minimal basis functions: {n}")
    except Exception as e:
        print("Error:", e)
