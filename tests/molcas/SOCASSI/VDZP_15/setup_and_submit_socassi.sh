#!/bin/bash
set -e

# Collect xyz files in increasing order
XYZ_FILES=($(ls po2_*.xyz | sort))
RASORB_FILES=($(ls system_*.RasOrb | sort))

N=${#XYZ_FILES[@]}

if [ "$N" -ne "${#RASORB_FILES[@]}" ]; then
  echo "ERROR: number of xyz files and RasOrb files does not match"
  exit 1
fi

echo "Found $N systems"

for ((i=0; i<N; i++)); do
  RUN=$(printf "run_%02d" $i)
  echo "Setting up $RUN"

  rm -rf $RUN
  mkdir -p $RUN
  cd $RUN

  # Copy and rename consistently
  cp ../"${XYZ_FILES[$i]}" po2.xyz
  cp ../"${RASORB_FILES[$i]}" system.RasOrb
  cp ../Po2_so_cassi.input .
  cp ../job_so_cassi.pbs .

  # Optional: customize PBS job name
  sed -i "s/^#PBS -N .*/#PBS -N Po2_SO_CASSI_${i}/" job_so_cassi.pbs

  # Submit
  qsub job_so_cassi.pbs

  cd ..
done

echo "All SO-CASSI jobs submitted 🚀"
