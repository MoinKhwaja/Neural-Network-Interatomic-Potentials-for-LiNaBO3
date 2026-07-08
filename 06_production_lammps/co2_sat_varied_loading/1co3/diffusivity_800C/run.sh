#!/bin/bash
#$ -cwd
#$ -l node_q=1
#$ -l h_rt=16:00:00
#$ -N diff_1co3_800C
#$ -o diff_1co3_800C.out
#$ -e diff_1co3_800C.err

source /gs/fs/tga-harada/Moin/deepmd/scripts/env_lammps.sh

lmp -in input.lammps
