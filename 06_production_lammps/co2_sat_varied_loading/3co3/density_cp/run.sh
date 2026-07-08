#!/bin/bash
#$ -cwd
#$ -l node_q=1
#$ -l h_rt=2:00:00
#$ -N den_3co3
#$ -o den_3co3.out
#$ -e den_3co3.err

source /gs/fs/tga-harada/Moin/deepmd/scripts/env_lammps.sh

lmp -in input.lammps
