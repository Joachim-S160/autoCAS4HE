#!/bin/bash
# Setup environment for autoCAS with patched Serenity
# Source this file: source setup_autocas_env.sh

# Activate Python environment
source /home/joaschee/autocas_env/bin/activate

# Serenity resources
export SERENITY_RESOURCES="/home/joaschee/serenity/data/"

# Default basis path (add custom paths before the colon if needed)
export SERENITY_BASIS_PATH="/home/joaschee/serenity/data/basis/"

# Library path for serenipy (MUST be set before Python starts)
export LD_LIBRARY_PATH="/home/joaschee/serenity/build/lib:$LD_LIBRARY_PATH"

# Add Serenity binary to PATH
export PATH="/home/joaschee/serenity/bin:$PATH"

echo "========================================"
echo "autoCAS4HE environment activated"
echo "========================================"
echo "  Python:            $(which python)"
echo "  SERENITY_RESOURCES: $SERENITY_RESOURCES"
echo "  SERENITY_BASIS_PATH: $SERENITY_BASIS_PATH"
echo "  Serenity binary:   $(which serenity 2>/dev/null || echo 'not found')"
echo "========================================"
