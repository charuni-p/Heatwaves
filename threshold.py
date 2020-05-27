import dask as da
from dask.distributed import LocalCluster, Client
from datetime import date
import glob
import numpy as np
import time
import xarray as xr
%pylab inline
local_dir = "/g/data/e14/cp3790/dask-workers" #Replace this with your local directory 
cluster = LocalCluster(processes=False, local_dir=local_dir)
client = Client(cluster)

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


files = sorted(glob.glob('/g/data/e14/cp3790/Charuni/ERA5-new/era5_dailytmax_*.nc'))

obs_aus = (xr.open_mfdataset(files, combine='nested', concat_dim='time', chunks={'latitude': 10})
           .sel(time=slice('1983', '2012'), longitude=slice(113, 154), latitude=slice(-10, -44)))
#baseline period for my calculation is 1983-2012
baseline_tmax = obs_aus["dmax"]
baseline_tmax.attrs['units'] = 'deg C'

reshaped_tmax = reshape_data(baseline_tmax)

start = reshaped_tmax[:31] # the first 31 days 
start['dayofyear'] = range(366,397) # the first 31 days will be 'stitched' to the last 31 days 
end = reshaped_tmax[-31:] # the last 31 days 
end['dayofyear'] = range(-30, 1) # the last 31 days will be 'stitched' to the first 31 days 
circular_tmax = xr.concat([end, reshaped_tmax, start], dim = 'dayofyear').chunk({'dayofyear' : 31})


percRolling = circular_tmax.rolling(dayofyear=15, center=True).construct('rolling_days')
# This takes in the circular_tmax, performs the percentile calculation, then creates a new dimension and coordinate names 
# to prepapre the data for the final output
stacked = percRolling.stack(z = ('rolling_days', 'year'))
rawPerc_data = da.array.apply_along_axis(np.nanpercentile, stacked.get_axis_num('z'), stacked.data, 90)
tmax_coords = circular_tmax.coords
new_coords = {name : tmax_coords[name] for name in tmax_coords if name != 'year'}
new_dims = [name for name in circular_tmax.dims if name != 'year']
rawPerc = xr.DataArray(rawPerc_data, coords = new_coords, dims = new_dims)

tmax_threshold = rawPerc.rolling(dayofyear=31, center = True).mean()
print("Data smoothed, DONE.")
tmax_threshold = tmax_threshold.isel(dayofyear = slice(31,-31))
print("First and last 31 days sliced")

xr.Dataset({'threshold': tmax_threshold}).to_netcdf('/g/data/e14/cp3790/Charuni/threshold-australia.nc',
                                              encoding={'threshold': 
                                                        {'chunksizes': (100, tmax_threshold.shape[1], tmax_threshold.shape[2]),
                                                         'zlib': True,
                                                         'shuffle': True, 
                                                         'complevel': 2}})
