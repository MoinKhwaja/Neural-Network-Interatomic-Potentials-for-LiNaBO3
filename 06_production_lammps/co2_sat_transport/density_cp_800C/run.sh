#!/bin/bash
#$ -cwd
#$ -l node_q=1
#$ -l h_rt=2:00:00
#$ -N pco2_den_800C
#$ -o den_800C.out
#$ -e den_800C.err

source /gs/fs/tga-harada/Moin/deepmd/scripts/env_lammps.sh

lmp -in input.lammps
