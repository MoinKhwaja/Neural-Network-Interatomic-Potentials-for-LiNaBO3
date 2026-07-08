#!/bin/bash
#$ -cwd
#$ -l node_q=1
#$ -l h_rt=12:00:00
#$ -N pco2_tc_600C
#$ -o tc_600C.out
#$ -e tc_600C.err

source /gs/fs/tga-harada/Moin/deepmd/scripts/env_lammps.sh

lmp -in input.lammps
