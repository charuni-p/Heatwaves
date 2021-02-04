#!/usr/bin/env python3

import dask
import xarray as xr
import os

indir='/g/data/ub4/era5/derived/1hr/wind10/'
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

wind10=ds.wind10

dailywind10=wind10.resample(time='1D').mean('time')

dailywind10.attrs = wind10.attrs
dailywind10.attrs['long_name'] = "Daily windspeed at 10m"

ds=xr.Dataset({'wind10':dailywind10})

ds.to_netcdf(f'era5_dailywind10_{year}.nc', 
        encoding={
            'wind10':{
                'zlib':True,
                'chunksizes':dailywind10.data.chunksize,
                'complevel':5,
                'shuffle':True
                }
            })