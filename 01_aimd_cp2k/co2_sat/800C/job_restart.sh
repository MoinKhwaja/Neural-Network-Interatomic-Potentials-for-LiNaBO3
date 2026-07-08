#!/bin/bash
#$ -cwd
#$ -N sat_rst_800C
#$ -l node_q=1
#$ -l h_rt=23:00:00
#$ -o cp2k_restart.out
#$ -e cp2k_restart.err
#$ -m be
#$ -M khwaja.m.aa@m.titech.ac.jp

module load cp2k/2024.1
export OMP_NUM_THREADS=48
export CUDA_VISIBLE_DEVICES=0

mpirun -np 1 --map-by ppr:1:node:pe=48 --bind-to core cp2k.psmp -i aimd_restart.inp -o aimd_restart.out
