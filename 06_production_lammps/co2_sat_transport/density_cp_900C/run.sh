#!/bin/bash
#$ -cwd
#$ -l node_q=1
#$ -l h_rt=2:00:00
#$ -N pco2_den_900C
#$ -o den_900C.out
#$ -e den_900C.err

source /gs/fs/tga-harada/Moin/deepmd/scripts/env_lammps.sh

lmp -in input.lammps
