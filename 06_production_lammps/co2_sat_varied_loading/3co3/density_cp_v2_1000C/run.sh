#!/bin/bash
#$ -cwd
#$ -l node_q=1
#$ -l h_rt=3:00:00
#$ -N v2_den_3co3_1000C
#$ -o den_3co3_1000C.out
#$ -e den_3co3_1000C.err

source /gs/fs/tga-harada/Moin/deepmd/scripts/env_lammps.sh

lmp -in input.lammps
