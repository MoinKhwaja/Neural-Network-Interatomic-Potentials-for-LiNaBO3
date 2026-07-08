#!/bin/bash
#$ -cwd
#$ -l node_q=1
#$ -l h_rt=24:00:00
#$ -N visc_700C
#$ -o visc_700C.out
#$ -e visc_700C.err
#$ -pe openmpi 1

CUSTOM_LMP=/gs/fs/tga-harada/Moin/deepmd/production/viscosity_600C/lammps-stable_2Aug2023_update3/build/lmp

module purge
module load deepmd-kit/2.2.9
export LAMMPS_PLUGIN_PATH=/apps/t4/rhel9/free/deepmd-kit/2.2.9/gcc11.4.1/cuda12.3.2/openmpi5.0.2/lib/deepmd_lmp
export OMP_NUM_THREADS=12
export CUDA_VISIBLE_DEVICES=0,1,2,3

cd /gs/fs/tga-harada/Moin/deepmd/production_v2/viscosity_nve_windows_700C
${CUSTOM_LMP} -in input.lammps > log.lammps 2>&1
