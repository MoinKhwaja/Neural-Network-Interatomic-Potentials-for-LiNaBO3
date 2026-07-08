#!/bin/bash
#$ -cwd
#$ -l node_q=1
#$ -l h_rt=6:00:00
#$ -N pv4_d_600C
#$ -o prod.out
#$ -e prod.err
#$ -pe openmpi 1

module purge
module load lammps/2aug2023_u3
module load deepmd-kit/2.2.9
export LAMMPS_PLUGIN_PATH=/apps/t4/rhel9/free/deepmd-kit/2.2.9/gcc11.4.1/cuda12.3.2/openmpi5.0.2/lib/deepmd_lmp
export OMP_NUM_THREADS=12
export CUDA_VISIBLE_DEVICES=0,1,2,3

cd /gs/fs/tga-harada/Moin/deepmd/production_pco2_v4/density_cp_600C
lmp -in input.lammps > log.lammps 2>&1
