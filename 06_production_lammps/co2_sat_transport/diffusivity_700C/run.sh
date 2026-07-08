#!/bin/bash
#$ -cwd
#$ -l node_q=1
#$ -l h_rt=16:00:00
#$ -N pco2_diff_700C
#$ -o diff_700C.out
#$ -e diff_700C.err

source /gs/fs/tga-harada/Moin/deepmd/scripts/env_lammps.sh

lmp -in input.lammps
