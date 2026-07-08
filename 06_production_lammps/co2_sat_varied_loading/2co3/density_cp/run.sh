#!/bin/bash
#$ -cwd
#$ -l node_q=1
#$ -l h_rt=2:00:00
#$ -N den_2co3
#$ -o den_2co3.out
#$ -e den_2co3.err

source /gs/fs/tga-harada/Moin/deepmd/scripts/env_lammps.sh

lmp -in input.lammps
