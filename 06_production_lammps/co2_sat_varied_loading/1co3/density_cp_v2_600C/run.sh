#!/bin/bash
#$ -cwd
#$ -l node_q=1
#$ -l h_rt=3:00:00
#$ -N v2_den_1co3_600C
#$ -o den_1co3_600C.out
#$ -e den_1co3_600C.err

source /gs/fs/tga-harada/Moin/deepmd/scripts/env_lammps.sh

lmp -in input.lammps
