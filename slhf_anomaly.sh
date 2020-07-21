#!/usr/bin/env bash
#PBS -P e14
#PBS -l walltime=0:14:00
#PBS -l mem=8GB
#PBS -q normal
#PBS -l ncpus=1
#PBS -l wd
#PBS -l storage=gdata/e14+gdata/hh5
module use /g/data/hh5/public/modules
module load conda/analysis3

python3 slhf_anomaly.py