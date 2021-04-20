#!/usr/bin/env python3

import dask
import xarray as xr
import os

indir='/g/data/rt52/era5/pressure-levels/reanalysis/q'
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

q=ds.q.sel(level=1000)

dailyq=q.resample(time='1D').mean('time')

dailyq.attrs = q.attrs
dailyq.attrs['long_name'] = "Daily mean specific humidity"

ds=xr.Dataset({'dailyq':dailyq})


outdir='/g/data/e14/cp3790/Charuni/NCI/ERA5-Q/'
ds.to_netcdf(f'{outdir}/era5_dailyq_{year}.nc', 
        encoding={
            'dailyq':{
                'zlib':True,
                'chunksizes':dailyq.data.chunksize,
                'complevel':5,
                'shuffle':True
                }
            })