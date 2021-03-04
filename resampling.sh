#!/usr/bin/env bash
#PBS -P e14
#PBS -l walltime=0:30:00
#PBS -l mem=7GB
#PBS -q normal
#PBS -l ncpus=1
#PBS -l wd
#PBS -l storage=gdata/e14+gdata/hh5+gdata/zz93
module use /g/data/hh5/public/modules
module load conda/analysis3
export YEAR=${YEAR:-2002}
python3 era5_t2m_resample.py