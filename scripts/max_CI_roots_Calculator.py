#!/usr/bin/env python3

"""
Script to calculate maximum number of CI roots for CASSCF/RASSCF calculations
Based on the number of configurations in the active space
"""

import sys
from math import comb

def calculate_max_roots(n_elec, n_orb, spin_mult):
    """
    Calculate maximum number of CI roots (CSFs/determinants)
    
    Args:
        n_elec: Number of active electrons
        n_orb: Number of active orbitals
        spin_mult: Spin multiplicity (2S+1)
    
    Returns:
        Maximum number of roots (configurations)
    """
    
    # Calculate number of unpaired electrons (2S where S = (mult-1)/2)
    n_unpaired = spin_mult - 1
    
    # Number of alpha and beta electrons
    n_alpha = (n_elec + n_unpaired) // 2
    n_beta = (n_elec - n_unpaired) // 2
    
    # Validation checks
    if n_alpha + n_beta != n_elec:
        print(f"ERROR: Invalid spin multiplicity {spin_mult} for {n_elec} electrons")
        print(f"  Calculated: {n_alpha} alpha + {n_beta} beta = {n_alpha+n_beta} electrons")
        return None
    
    if n_alpha > n_orb or n_beta > n_orb:
        print(f"ERROR: Number of electrons exceeds orbital capacity")
        print(f"  Alpha electrons: {n_alpha}, Beta electrons: {n_beta}")
        print(f"  Available orbitals: {n_orb}")
        return None
    
    if n_alpha < 0 or n_beta < 0:
        print(f"ERROR: Negative number of electrons calculated")
        return None
    
    # Calculate number of determinants: C(n_orb, n_alpha) * C(n_orb, n_beta)
    try:
        alpha_configs = comb(n_orb, n_alpha)
        beta_configs = comb(n_orb, n_beta)
        max_configs = alpha_configs * beta_configs
        
        return max_configs, n_alpha, n_beta, alpha_configs, beta_configs
    except (ValueError, OverflowError) as e:
        print(f"ERROR: Calculation failed: {e}")
        return None

def main():
    print("=" * 50)
    print("  Maximum CI Roots Calculator")
    print("=" * 50)
    print()
    
    # Get input
    try:
        if len(sys.argv) == 4:
            # Command line arguments
            n_electrons = int(sys.argv[1])
            n_orbitals = int(sys.argv[2])
            spin_multiplicity = int(sys.argv[3])
        else:
            # Interactive input
            n_electrons = int(input("Enter number of active electrons: "))
            n_orbitals = int(input("Enter number of active orbitals: "))
            spin_multiplicity = int(input("Enter spin multiplicity: "))
    except ValueError:
        print("ERROR: Please enter valid integers")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nAborted by user")
        sys.exit(0)
    
    print()
    print("Input:")
    print(f"  Active electrons: {n_electrons}")
    print(f"  Active orbitals: {n_orbitals}")
    print(f"  Spin multiplicity: {spin_multiplicity}")
    print()
    
    # Validate basic inputs
    if n_electrons > 2 * n_orbitals:
        print("ERROR: Too many electrons for the number of orbitals!")
        print(f"Maximum electrons for {n_orbitals} orbitals: {2 * n_orbitals}")
        sys.exit(1)
    
    if n_electrons < 0 or n_orbitals < 0 or spin_multiplicity < 1:
        print("ERROR: All inputs must be positive")
        sys.exit(1)
    
    # Check spin multiplicity validity
    n_unpaired = spin_multiplicity - 1
    if (n_electrons % 2) != (n_unpaired % 2):
        print(f"ERROR: Spin multiplicity {spin_multiplicity} is not compatible with {n_electrons} electrons")
        print("For even number of electrons, spin multiplicity must be odd (1=singlet, 3=triplet, 5=quintet, etc.)")
        print("For odd number of electrons, spin multiplicity must be even (2=doublet, 4=quartet, etc.)")
        sys.exit(1)
    
    # Calculate maximum roots
    result = calculate_max_roots(n_electrons, n_orbitals, spin_multiplicity)
    
    if result is None:
        sys.exit(1)
    
    max_roots, n_alpha, n_beta, alpha_configs, beta_configs = result
    
    print("=" * 50)
    print("Results:")
    print("=" * 50)
    print(f"  Alpha electrons: {n_alpha}")
    print(f"  Beta electrons: {n_beta}")
    print(f"  Alpha configurations: C({n_orbitals},{n_alpha}) = {alpha_configs:,}")
    print(f"  Beta configurations: C({n_orbitals},{n_beta}) = {beta_configs:,}")
    print()
    print(f"Maximum number of CI roots: {max_roots:,}")
    print()
    print("=" * 50)
    print("Recommendation:")
    print("=" * 50)
    
    if max_roots > 100:
        print(f"  - You can request up to {max_roots:,} roots")
        print("  - For practical calculations, consider 10-50 roots")
        print(f"  - Safe choice: {min(50, max_roots)} roots")
    elif max_roots > 20:
        print(f"  - You can request up to {max_roots} roots")
        print(f"  - Safe choice: {max_roots - 5} roots (leaving some margin)")
    else:
        print(f"  - You can request up to {max_roots} roots")
        print(f"  - WARNING: Very limited configuration space!")
        print(f"  - Recommend requesting at most {max(1, max_roots - 2)} roots")
    print()
    
    # Specific warning for small spaces
    if max_roots < 10:
        print("⚠️  WARNING: Your active space is very constrained!")
        print("   Consider:")
        print("   - Reducing spin multiplicity if possible")
        print("   - Increasing number of active orbitals")
        print("   - Reducing number of active electrons")
        print()

if __name__ == "__main__":
    main()
