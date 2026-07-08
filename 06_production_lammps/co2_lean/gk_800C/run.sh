#!/bin/bash
#$ -cwd
#$ -l node_q=1
#$ -l h_rt=8:00:00
#$ -N gk_lean_800
#$ -o gk_lean_800.out
#$ -e gk_lean_800.err

source /gs/fs/tga-harada/Moin/deepmd/scripts/env_lammps.sh

lmp -in input.lammps
