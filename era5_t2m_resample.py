#!/usr/bin/env python3

import dask
import xarray as xr
import os

indir='/g/data/zz93/era5-land/reanalysis/2t'
year=int(os.getenv('YEAR', '2002'))

ds = xr.open_mfdataset(
        f'{indir}/{year}/*.nc',
        combine='by_coords',
        chunks={
            'time':93,
            'latitude':91,
            'longitude':180
            }
        )

# Update chunking
#for v in ds:
#    if 'chunksizes' in ds[v].encoding:
#        ds[v] = ds[v].chunk(ds[v].encoding['chunksizes'])

t2m=ds.t2m

dailytmax=t2m.resample(time='1D').max('time')

dailytmax.attrs = t2m.attrs
dailytmax.attrs['long_name'] = "Daily maximum temperature at 2m"

ds=xr.Dataset({'dailytmax':dailytmax})


outdir='/g/data/e14/cp3790/Charuni/NCI/ERA5-T2M/'
ds.to_netcdf(f'{outdir}/era5_dailytmax_{year}.nc', 
        encoding={
            'dailytmax':{
                'zlib':True,
                'chunksizes':dailytmax.data.chunksize,
                'complevel':5,
                'shuffle':True
                }
            })