#!/bin/bash
#$ -cwd
#$ -l node_q=1
#$ -l h_rt=2:00:00
#$ -N pco2_den_700C
#$ -o den_700C.out
#$ -e den_700C.err

source /gs/fs/tga-harada/Moin/deepmd/scripts/env_lammps.sh

lmp -in input.lammps
