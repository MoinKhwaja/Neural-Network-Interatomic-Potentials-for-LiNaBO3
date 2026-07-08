#!/bin/bash
module purge
module load cp2k/2024.1
export OMP_NUM_THREADS=12
export CUDA_VISIBLE_DEVICES=0,1,2,3
