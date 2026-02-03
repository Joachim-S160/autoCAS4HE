# autoCAS4HE - autoCAS for Heavy Elements

Patched versions of [Serenity](https://github.com/qcserenity/serenity) and [autoCAS](https://github.com/qcscine/autocas) enabling automated active space selection for heavy element systems (Z > 36) using relativistic orbitals from OpenMolcas.

Related issues:
- [qcserenity/serenity#18](https://github.com/qcserenity/serenity/issues/18)
- [qcscine/autocas#18](https://github.com/qcscine/autocas/issues/18)

---

## Pipeline Overview

Heavy elements require scalar relativistic Hamiltonians (DKH2) that Serenity does not support. The solution uses OpenMolcas for SCF and feeds those orbitals into Serenity for localization:

```
OpenMolcas (DKH2 SCF)
    → Serenity (IBO localization)
        → autoCAS (active space selection)
            → OpenMolcas (CASSCF/DMRGSCF)
```

---

## Key Patches

### Serenity
- Custom basis set support via `SERENITY_BASIS_PATH`
- Increased primitive limit for ANO-RCC basis sets
- Energy-based Rydberg orbital classification (fixes IBO overflow for heavy elements)
- Expanded MINAO basis for Z >= 37 (from ANO-RCC)

### autoCAS
- External orbital workflow (`-e/--external-orbitals`)
- Localization method selection (`-L/--localization`)
- Force CAS option (`-f/--force-cas`)
- IBO distribution plotting

---

## Quick Start

### 1. Clone with submodules

```bash
git clone --recurse-submodules https://github.com/Joachim-S160/autoCAS4HE.git
cd autoCAS4HE
```

### 2. Build Serenity

```bash
cd serenity
mkdir build && cd build
cmake -G Ninja .. \
  -DSERENITY_PYTHON=ON \
  -DSERENITY_PYTHON_BINDINGS=ON \
  -DBUILD_TESTING=OFF \
  -DCMAKE_BUILD_TYPE=Release
ninja -j1
cd ../..
```

### 3. Set up environment

```bash
source setup_autocas_env.sh
```

### 4. Run tests

**Light elements (standard workflow):**
```bash
cd tests/autocas/serenity_scf/N2_test
scine_autocas_consistent_active_space -i 1 n2_0.xyz n2_1.xyz
```

**Heavy elements (external orbitals from OpenMolcas):**
```bash
cd tests/autocas/external_scf/Po2_test
scine_autocas_consistent_active_space \
  -e -o po2_0.scf.h5,po2_1.scf.h5 \
  -b ANO-RCC-VDZP \
  -f \
  po2_0.xyz po2_1.xyz
```

---

## CLI Options

| Flag | Description |
|------|-------------|
| `-e` | Use external orbitals (skip Serenity SCF) |
| `-o` | Comma-separated list of orbital files (.scf.h5) |
| `-b` | Basis set name |
| `-L` | Localization method (IBO, PIPEK_MEZEY, BOYS, EDMINSTON_RUEDENBERG) |
| `-f` | Force CAS selection even if system appears single-reference |
| `-i` | Number of DMRG iterations |

---

## Documentation

- [docs/ENVIRONMENT_SETUP.md](docs/ENVIRONMENT_SETUP.md) — Local/WSL setup
- [docs/HPC_BUILD_HORTENSE.md](docs/HPC_BUILD_HORTENSE.md) — HPC build guide
- [tests/README.md](tests/README.md) — Test directory overview

---

## License

- Serenity: LGPL-3.0
- autoCAS: BSD-3-Clause