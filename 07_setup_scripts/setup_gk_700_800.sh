#!/bin/bash
# Spawn GK 700 C and 800 C runs for all 5 compositions by cloning the
# existing 600 C setups and rewriting TEMP. Up to 10 new jobs total.
set -e
ROOT=/gs/fs/tga-harada/Moin/deepmd

# Source dirs keyed by composition shortname
declare -A SRC=(
  [lean]="$ROOT/production_v2/gk_600C"
  [1co3]="$ROOT/production_post_co2_varied/1co3/gk_600C"
  [2co3]="$ROOT/production_post_co2_varied/2co3/gk_600C"
  [3co3]="$ROOT/production_post_co2_varied/3co3/gk_600C"
  [4co3]="$ROOT/production_post_co2/gk_600C"
)

# Job-name shortcut
declare -A JOB=(
  [lean]="lean"
  [1co3]="1co3"
  [2co3]="2co3"
  [3co3]="3co3"
  [4co3]="4co3"
)

for comp in lean 1co3 2co3 3co3 4co3; do
  src_dir="${SRC[$comp]}"
  parent="$(dirname "$src_dir")"
  for T in 700 800; do
    new_dir="$parent/gk_${T}C"
    if [ -d "$new_dir" ] && [ -f "$new_dir/stress_corr.dat" ]; then
      echo "skip (already exists): $new_dir"
      continue
    fi
    mkdir -p "$new_dir"
    cp -n "$src_dir/conf.lmp" "$new_dir/"
    cp -n "$src_dir/frozen_model.pb" "$new_dir/"
    # input.lammps with TEMP rewritten to <T>+273.15
    TEMP_K=$(python3 -c "print(${T}+273.15)")
    sed -e "s/variable        TEMP equal 873.15/variable        TEMP equal ${TEMP_K}/" \
        -e "s/Green-Kubo bulk viscosity at 600C/Green-Kubo bulk viscosity at ${T}C/" \
        -e "s/(873.15K)/(${TEMP_K}K)/" \
        "$src_dir/input.lammps" > "$new_dir/input.lammps"
    # run.sh with new job name
    cat > "$new_dir/run.sh" <<EOF
#!/bin/bash
#\$ -cwd
#\$ -l node_q=1
#\$ -l h_rt=8:00:00
#\$ -N gk_${JOB[$comp]}_${T}
#\$ -o gk_${JOB[$comp]}_${T}.out
#\$ -e gk_${JOB[$comp]}_${T}.err

source $ROOT/scripts/env_lammps.sh

lmp -in input.lammps
EOF
    chmod +x "$new_dir/run.sh"
    echo "created: $new_dir"
  done
done

echo "Done. Use ./submit_gk_700_800.sh to submit all 10 jobs."
