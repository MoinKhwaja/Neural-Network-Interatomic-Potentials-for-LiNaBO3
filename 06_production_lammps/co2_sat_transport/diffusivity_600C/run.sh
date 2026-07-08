#!/bin/bash
#$ -cwd
#$ -l node_q=1
#$ -l h_rt=16:00:00
#$ -N pco2_diff_600C
#$ -o diff_600C.out
#$ -e diff_600C.err

source /gs/fs/tga-harada/Moin/deepmd/scripts/env_lammps.sh

lmp -in input.lammps
