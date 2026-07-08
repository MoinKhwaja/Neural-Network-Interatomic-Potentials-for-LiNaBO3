#!/bin/bash
#$ -cwd
#$ -l node_q=1
#$ -l h_rt=12:00:00
#$ -N tc3_v2
#$ -o tc_3co3_v2.out
#$ -e tc_3co3_v2.err

source /gs/fs/tga-harada/Moin/deepmd/scripts/env_lammps.sh

lmp -in input.lammps
