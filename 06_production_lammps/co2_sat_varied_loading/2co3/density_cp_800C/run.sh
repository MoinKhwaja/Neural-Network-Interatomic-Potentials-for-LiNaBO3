#!/bin/bash
#$ -cwd
#$ -l node_q=1
#$ -l h_rt=3:00:00
#$ -N den_2co3_800C
#$ -o den_2co3_800C.out
#$ -e den_2co3_800C.err

source /gs/fs/tga-harada/Moin/deepmd/scripts/env_lammps.sh

lmp -in input.lammps
