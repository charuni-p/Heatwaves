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

if __name__ == '__main__':
    climtas.nci.GadiClient()
    ds = xr.open_dataset('/g/data/e14/cp3790/Charuni/Heatwaves/windspeed.nc').sel(time=slice('1982', '2018'))
    windspeed = ds.windspeed
    windspeed_climatology = xr.open_dataarray('/g/data/e14/cp3790/Charuni/Heatwaves/windspeed_clim.nc', chunks={'dayofyear': None})
    anomaly = windspeed.groupby('time.dayofyear') - windspeed_climatology
    climtas.io.to_netcdf_throttled(anomaly.to_dataset(name='windspeed_anomaly'), '/g/data/e14/cp3790/Charuni/Heatwaves/windspeed_anom.nc') 