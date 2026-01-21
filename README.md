# autoCAS4HE - autoCAS for Heavy Elements

This repository provides a patched version of [Serenity](https://github.com/qcserenity/serenity) that enables using custom basis sets in Turbomole format (such as ANO-RCC-QVZP) for heavy element calculations with [autoCAS](https://github.com/qcscine/autocas).

## Problem

The standard Serenity installation has two issues that prevent using custom basis sets like ANO-RCC-QVZP for heavy elements:

1. **Limited basis set search paths**: Serenity only looks for basis sets in a single directory
2. **Primitive limit too low**: The `N_PRIM_MAX` constant was set to 23, but ANO-RCC basis sets require up to 25 primitives per basis function
3. **Silent fallback**: When a basis set isn't found, Serenity silently falls back to CC-PVDZ instead of raising an error

Related issues:
- [qcserenity/serenity#18](https://github.com/qcserenity/serenity/issues/18)
- [qcscine/autocas#18](https://github.com/qcscine/autocas/issues/18)

## Solution

This fork includes three modifications to Serenity:

### 1. `src/basis/BasisFunctionProvider.cpp`
- Added support for colon-separated search paths via `SERENITY_BASIS_PATH`
- Improved error messages showing which directories were searched

### 2. `src/integrals/wrappers/Libint.h`
- Increased `N_PRIM_MAX` from 23 to 25 to support ANO-RCC basis sets

### 3. `src/system/SystemController.cpp`
- Added `SERENITY_BASIS_PATH` environment variable support
- Falls back to `SERENITY_RESOURCES/basis/` for backwards compatibility

## Installation

### Clone with submodule

```bash
git clone --recurse-submodules https://github.com/Joachim-S160/autoCAS4HE.git
cd autoCAS4HE
```

### Build Serenity

```bash
cd serenity
mkdir build && cd build
cmake ..
ninja  # or make -j$(nproc)
```

### Set environment variables

```bash
# Point to custom basis sets directory (colon-separated for multiple dirs)
export SERENITY_BASIS_PATH="/path/to/custom/basis:/path/to/serenity/data/basis"

# Or use the traditional single directory
export SERENITY_RESOURCES="/path/to/serenity/data/"
```

## Usage with autoCAS

Once Serenity is built with these patches, you can use autoCAS with custom basis sets:

1. Place your Turbomole-format basis set files in a directory
2. Set `SERENITY_BASIS_PATH` to include that directory
3. Run autoCAS with your custom basis set name

## Custom Basis Sets

Basis set files should be in Turbomole format. The filename should match the basis set name in UPPERCASE (e.g., `ANO-RCC-QVZP`).

## Testing

TODO: Add test cases using ANO-RCC-QVZP basis set for heavy elements

## License

Serenity is licensed under LGPL-3.0. See the [serenity/LICENSE](serenity/LICENSE) file for details.
