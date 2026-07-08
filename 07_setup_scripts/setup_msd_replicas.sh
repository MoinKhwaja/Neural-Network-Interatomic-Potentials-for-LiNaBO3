#!/bin/bash
# Replica MSD runs at 700/800 C for all 5 compositions, different
# velocity seed than the original runs. Gives a 2nd independent
# trajectory per (n, T) so D values can be averaged.
set -e
ROOT=/gs/fs/tga-harada/Moin/deepmd
NEW_SEED=13579

declare -A SRC=(
  [lean_700]="$ROOT/production_v2/diffusivity_700C"
  [lean_800]="$ROOT/production_v2/diffusivity_800C"
  [1co3_700]="$ROOT/production_post_co2_varied/1co3/diffusivity_700C"
  [1co3_800]="$ROOT/production_post_co2_varied/1co3/diffusivity_800C"
  [2co3_700]="$ROOT/production_post_co2_varied/2co3/diffusivity_700C"
  [2co3_800]="$ROOT/production_post_co2_varied/2co3/diffusivity_800C"
  [3co3_700]="$ROOT/production_post_co2_varied/3co3/diffusivity_700C"
  [3co3_800]="$ROOT/production_post_co2_varied/3co3/diffusivity_800C"
  [4co3_700]="$ROOT/production_post_co2/diffusivity_700C"
  [4co3_800]="$ROOT/production_post_co2/diffusivity_800C"
)

for key in "${!SRC[@]}"; do
  src_dir="${SRC[$key]}"
  new_dir="${src_dir}_r2"
  if [ -d "$new_dir" ] && [ -f "$new_dir/msd.dat" ]; then
    echo "skip (already complete): $new_dir"
    continue
  fi
  mkdir -p "$new_dir"
  cp -n "$src_dir/conf.lmp" "$new_dir/"
  cp -n "$src_dir/frozen_model.pb" "$new_dir/"
  # Substitute velocity seed
  sed -E "s/(velocity[[:space:]]+all create \\\$\\{TEMP\\} )[0-9]+/\1${NEW_SEED}/" \
      "$src_dir/input.lammps" > "$new_dir/input.lammps"
  # Generate run.sh with replica job name and corrected cwd
  basename_src=$(basename "$src_dir")
  job_name="msd_${key}_r2"
  cat > "$new_dir/run.sh" <<EOF
#!/bin/bash
#\$ -cwd
#\$ -l node_q=1
#\$ -l h_rt=23:00:00
#\$ -N ${job_name}
#\$ -o ${job_name}.out
#\$ -e ${job_name}.err
#\$ -pe openmpi 1

CUSTOM_LMP=$ROOT/production/viscosity_600C/lammps-stable_2Aug2023_update3/build/lmp

module purge
module load deepmd-kit/2.2.9
export LAMMPS_PLUGIN_PATH=/apps/t4/rhel9/free/deepmd-kit/2.2.9/gcc11.4.1/cuda12.3.2/openmpi5.0.2/lib/deepmd_lmp
export OMP_NUM_THREADS=12
export CUDA_VISIBLE_DEVICES=0,1,2,3

cd ${new_dir}
\${CUSTOM_LMP} -in input.lammps > log.lammps 2>&1
EOF
  chmod +x "$new_dir/run.sh"
  echo "created: $new_dir"
done
