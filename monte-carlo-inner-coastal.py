#!/usr/bin/env python3

import climtas
import climtas.nci
from dask.distributed import LocalCluster, Client
import numpy as np
import xarray as xr

if __name__ == '__main__':
# opening the input files with heatwave severity data 
    thw = xr.open_dataset('/g/data/e14/cp3790/Charuni/Tasmania/new-coastal-may-2021.nc', chunks={'time':31, 'latitude': 25, 'longitude':10})
    mhw = xr.open_dataset('/g/data/e14/cp3790/Charuni/Tasmania/new-ocean-may-2021.nc', chunks={'time':31, 'latitude': 25, 'longitude':10})

# using severity>1 to redefine data array as heatwave(1) and non-heatwave(0) days  
    thw_da = xr.where(thw['severity'] > 1.0, 1, 0)
    mhw_da = xr.where(mhw['severity'] > 1.0, 1, 0)
    
# First we compute the series of random numbers 
# Use Nrepeats =100 to start with and then change to 10000 to compute the correct results
    Ntime = thw_da.sizes["time"]
    Nrepeats=100
    r_arr = np.random.randint(Ntime-1,size=Nrepeats)
    
    proportion_rand = xr.DataArray(np.ndarray([Nrepeats,thw_da.sizes['latitude'],thw_da.sizes['longitude']]),
                               dims=("Repeats","latitude","longitude"),
                               coords={"latitude":thw_da["latitude"],
                                       "longitude":thw_da["longitude"],
                                       "Repeats":np.arange(Nrepeats)
                                      }
                              )
# Monte carlo simulation where the THW timeseries is randomized and the proportion of co-occurring HW days is recalculated for each simulation     
    for i,r in enumerate(r_arr): 
        thw_ = thw_da.roll(time=r,roll_coords=False)
        co_occ = thw_.where(np.logical_and(thw_==1,mhw_da==1)).count(dim="time")
        non_co_occ = thw_.where(thw_==1).count(dim="time") 
        proportion_rand.loc[{"Repeats":i}] = co_occ/non_co_occ

# 100 simulations saved as a netcdf file 
    climtas.io.to_netcdf_throttled(proportion_rand.to_dataset(name='proportion_rand'), '/g/data/e14/cp3790/Charuni/Tasmania/proportion_rand_coastal.nc')