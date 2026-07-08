#!/bin/bash
#$ -cwd
#$ -l node_q=1
#$ -l h_rt=23:00:00
#$ -N msd_1co3_800_r2
#$ -o msd_1co3_800_r2.out
#$ -e msd_1co3_800_r2.err
#$ -pe openmpi 1

CUSTOM_LMP=/gs/fs/tga-harada/Moin/deepmd/production/viscosity_600C/lammps-stable_2Aug2023_update3/build/lmp

module purge
module load deepmd-kit/2.2.9
export LAMMPS_PLUGIN_PATH=/apps/t4/rhel9/free/deepmd-kit/2.2.9/gcc11.4.1/cuda12.3.2/openmpi5.0.2/lib/deepmd_lmp
export OMP_NUM_THREADS=12
export CUDA_VISIBLE_DEVICES=0,1,2,3

cd /gs/fs/tga-harada/Moin/deepmd/production_post_co2_varied/1co3/diffusivity_800C_r2
${CUSTOM_LMP} -in input.lammps > log.lammps 2>&1
