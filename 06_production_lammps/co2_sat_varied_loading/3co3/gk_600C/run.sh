#!/bin/bash
#$ -cwd
#$ -l node_q=1
#$ -l h_rt=8:00:00
#$ -N gk_3co3
#$ -o gk_3co3.out
#$ -e gk_3co3.err

source /gs/fs/tga-harada/Moin/deepmd/scripts/env_lammps.sh

lmp -in input.lammps
