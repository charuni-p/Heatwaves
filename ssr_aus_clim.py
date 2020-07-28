#!/usr/bin/env python3

import climtas
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
    files = sorted(glob.glob('/g/data/e14/cp3790/Charuni/ERA5-SSR/era5_dailyssr_*.nc'))

    ds = xr.open_mfdataset(files, combine='by_coords', chunks={'time':None}).sel(time=slice('1983', '2012'), longitude=slice(90, 180), latitude=slice(0, -60))
    ssr = ds['ssr']/1000000
    ssr.attrs['units'] = 'MJm-2'

    reshaped_ssr = reshape_data(ssr)
    start = reshaped_ssr[:31] # the first 31 days 
    start['dayofyear'] = range(366,397) # the first 31 days will be 'stitched' to the last 31 days 
    end = reshaped_ssr[-31:] # the last 31 days 
    end['dayofyear'] = range(-30, 1) # the last 31 days will be 'stitched' to the first 31 days 
    circular_ssr = xr.concat([end, reshaped_ssr, start], dim = 'dayofyear').chunk({'dayofyear' : 31})

    raw_ssr = circular_ssr.mean('year')
    ssr_climatology_smooth = raw_ssr.rolling(dayofyear = 15, center = True).mean() # smoothen it once with a 15-day rolling window
    ssr_climatology_smoother = ssr_climatology_smooth.rolling(dayofyear = 31, center = True).mean() # smoothen it again by running a 31-day window 
    ssr_climatology = ssr_climatology_smoother.isel(dayofyear = slice(31,-31)) # drop the first and last 31 day

    climtas.io.to_netcdf_throttled(ssr_climatology.to_dataset(name='ssr_climatology'), '/g/data/e14/cp3790/Charuni/Heatwaves/ssr_clim.nc')
    