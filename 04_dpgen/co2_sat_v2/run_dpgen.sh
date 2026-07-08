#!/bin/bash
#$ -cwd
#$ -N dpgen_pco2v2
#$ -l node_o=1
#$ -l h_rt=23:55:00
#$ -o dpgen_pco2_v2.out
#$ -e dpgen_pco2_v2.err
#$ -m be
#$ -M khwaja.m.aa@m.titech.ac.jp

export PATH=/gs/fs/tga-harada/Moin/deepmd/bin:/apps/t4/rhel9/uge/latest/bin/lx-amd64:$PATH

source ~/miniconda3/etc/profile.d/conda.sh
conda activate /gs/fs/tga-harada/Moin/conda/envs/deepmd

cd /gs/fs/tga-harada/Moin/deepmd/dpgen_post_co2_v2

dpgen run param.json machine.json
