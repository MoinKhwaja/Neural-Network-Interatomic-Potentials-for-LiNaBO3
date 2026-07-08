#!/bin/bash
#$ -cwd
#$ -l node_q=1
#$ -l h_rt=16:00:00
#$ -N diff_2co3_700C
#$ -o diff_2co3_700C.out
#$ -e diff_2co3_700C.err

source /gs/fs/tga-harada/Moin/deepmd/scripts/env_lammps.sh

lmp -in input.lammps
