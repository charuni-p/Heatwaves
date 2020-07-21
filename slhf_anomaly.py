#!/usr/bin/env python3

import dask as da
from dask.distributed import LocalCluster, Client
from datetime import date
import glob
import numpy as np
import time
import xarray as xr

def fix(ds):
    # This was the code fixed to make the clim and thresh repeatable so that the shapes of clim, thresh and obs are equal.
    trial = ds
    i = 0
    while i < 37:  # <-- Here, 37 corresponds to the number of years in obs dataset 
        trial = xr.concat([trial, ds], 'dayofyear')
        i+=1
    trial = trial.isel(dayofyear = slice(0,13514))
    # to specify the dates/time 
    trial.coords['dayofyear'] = np.arange(date(1982,1,1).toordinal(),date(2018,12,31).toordinal()+1) 
    
    # This code was used to rename the dayofyear dimension to time.
    trial['time'] = trial['dayofyear']
    del trial['dayofyear']
    trial = trial.rename({'dayofyear': 'time'})
    
    t = np.arange(date(1982,1,1).toordinal(),date(2018,12,31).toordinal()+1)
    dates = [date.fromordinal(tt.astype(int)) for tt in t]
    
    trial.coords['time'] = dates

    return trial

files = sorted(glob.glob('/g/data/e14/cp3790/Charuni/ERA5-SLHF/era5_dailyslhf_*.nc'))
ds = xr.open_mfdataset(files, combine='by_coords').sel(time=slice('1982', '2018'), longitude=slice(90, 180), latitude=slice(0, -60))
obs_slhf = ds.slhf

slhf_climatology = xr.open_dataarray('/g/data/e14/cp3790/Charuni/Heatwaves/slhf-clim-aus.nc')
fixed_climatology = fix(slhf_climatology)

anomaly = obs_slhf - fixed_climatology

xr.Dataset({'anomaly': anomaly}).to_netcdf('/g/data/e14/cp3790/Charuni/Heatwaves/slhf-anomaly-aus.nc',
                                              encoding={'anomaly': 
                                                        {'chunksizes': (1000, anomaly.shape[1], anomaly.shape[2]),
                                                         'zlib': True,
                                                         'shuffle': True, 
                                                         'complevel': 2}}) 