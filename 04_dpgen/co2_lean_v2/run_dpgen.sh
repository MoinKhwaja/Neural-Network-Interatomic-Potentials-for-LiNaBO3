#!/bin/bash
#$ -cwd
#$ -l node_o=1
#$ -l h_rt=24:00:00
#$ -N dpgen_v2
#$ -o dpgen_v2.out
#$ -e dpgen_v2.err
#$ -pe openmpi 1

module purge
export PATH=/gs/fs/tga-harada/Moin/deepmd/bin:/gs/fs/tga-harada/Moin/conda/envs/deepmd/bin:/apps/t4/rhel9/uge/latest/bin/lx-amd64:$PATH

cd /gs/fs/tga-harada/Moin/deepmd/dpgen_v2
dpgen run param.json machine.json 2>&1 | tee dpgen_run.log
