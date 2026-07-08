#!/bin/bash
module purge
module load deepmd-kit/2.2.9
export OMP_NUM_THREADS=12
export CUDA_VISIBLE_DEVICES=0,1,2,3
