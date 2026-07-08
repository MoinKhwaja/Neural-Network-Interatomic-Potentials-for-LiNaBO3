#!/bin/bash
module purge
module load lammps/2aug2023_u3
module load deepmd-kit/2.2.9
export LAMMPS_PLUGIN_PATH=/apps/t4/rhel9/free/deepmd-kit/2.2.9/gcc11.4.1/cuda12.3.2/openmpi5.0.2/lib/deepmd_lmp
export OMP_NUM_THREADS=12
export CUDA_VISIBLE_DEVICES=0,1,2,3
