#!/usr/bin/env python3

import climtas.nci
import dask as da
from dask.distributed import LocalCluster, Client
from datetime import date
import glob
import numpy as np
import time
import xarray as xr


def reshape_data(da):
        da_groupby = list(da.groupby('time.dayofyear'))
        dayofyear = []
        da_dayofyear = []
        for item in list(da_groupby):
            dayofyear.append(item[0])
            da_tmp = item[1]
            da_tmp['time'] = da_tmp['time.year']
            da_tmp = da_tmp.rename({'time': 'year'})
            da_tmp = da_tmp.assign_coords(dayofyear=item[0])
            da_dayofyear.append(da_tmp)
        da_reshaped = xr.concat(da_dayofyear, dim='dayofyear')
        return da_reshaped

if __name__ == '__main__':
    climtas.nci.GadiClient()
    files = sorted(glob.glob('/g/data/e14/cp3790/Charuni/ERA5-MSL/era5_dailymsl_*.nc'))

    ds = xr.open_mfdataset(files, combine='by_coords', chunks={'time':None}).sel(time=slice('1983', '2012'))
    dmsl = ds['dmsl']/1000
    dmsl.attrs['units'] = 'hPa'

    reshaped_msl = reshape_data(dmsl)
    start = reshaped_msl[:31] # the first 31 days 
    start['dayofyear'] = range(366,397) # the first 31 days will be 'stitched' to the last 31 days 
    end = reshaped_msl[-31:] # the last 31 days 
    end['dayofyear'] = range(-30, 1) # the last 31 days will be 'stitched' to the first 31 days 
    circular_msl = xr.concat([end, reshaped_msl, start], dim = 'dayofyear').chunk({'dayofyear' : 31})

    raw_msl = circular_msl.mean('year')
    msl_climatology_smooth = raw_msl.rolling(dayofyear = 15, center = True).mean() # smoothen it once with a 15-day rolling window
    msl_climatology_smoother = msl_climatology_smooth.rolling(dayofyear = 31, center = True).mean() # smoothen it again by running a 31-day window 
    msl_climatology = msl_climatology_smoother.isel(dayofyear = slice(31,-31)) # drop the first and last 31 day

    xr.Dataset({'climatology': msl_climatology}).to_netcdf('/g/data/e14/cp3790/Charuni/Heatwaves/msl-clim-global.nc',
                                              encoding={'climatology': 
                                                        {'chunksizes': (100, msl_climatology.shape[1], msl_climatology.shape[2]),
                                                         'zlib': True,
                                                         'shuffle': True, 
                                                         'complevel': 2}}) 