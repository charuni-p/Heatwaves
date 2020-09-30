import climtas
import climtas.nci
import numpy as np
import pandas as pd
import xarray as xr

if __name__ == '__main__':
    climtas.nci.GadiClient()
    thw = xr.open_dataset('/g/data/e14/cp3790/Charuni/Tasmania/aus-coastal-sev.nc')
    mhw = xr.open_dataset('/g/data/e14/cp3790/Charuni/Tasmania/aus-ocean-sev-2.nc')
    
    thw_events = climtas.event.find_events(thw.severity > 1, min_duration = 3)

    def get_coords(da, events):
    # Convert the index values to coordinates
        coords = {}
        for d in da.dims:
            coords[d] = da[d].values[events[d].values]
    
    # Also work out when the event ends
        coords['time_end'] = da['time'].values[events['time'].values + events['event_duration'].values-1]
        #coords['event_duration'] = coords['time_end'] - coords['time'] 
        coords['event_duration'] = events['event_duration'].values
    
        return pd.DataFrame(coords, index=events.index)

    thw_new = get_coords(thw, thw_events)

    thw_new_df = thw_new.reset_index()
    thw_new_df.set_index(['latitude', 'longitude'], inplace=True)
    
    mhw_events = climtas.event.find_events(mhw.severity > 1, min_duration = 5)
    
    mhw_new = get_coords(mhw, mhw_events)

    mhw_new_df = mhw_new.reset_index()
    mhw_new_df.set_index(['latitude', 'longitude'], inplace=True)
    
    df_merge_col = pd.merge(thw_new_df, mhw_new_df, on=['latitude', 'longitude'])

    del df_merge_col['index_y']
    del df_merge_col['index_x']
    
    from datetime import datetime
    from collections import namedtuple
    Range = namedtuple('Range', ['start', 'end'])
    overlap = []
    for n in range (df_merge_col.shape[0]):
        mhw = Range(start=df_merge_col['time_y'][n], end=df_merge_col['time_end_y'][n])
        thw = Range(start=df_merge_col['time_x'][n], end=df_merge_col['time_end_x'][n])
        latest_start = max(mhw.start, thw.start)
        earliest_end = min(mhw.end, thw.end)
        delta = (earliest_end - latest_start).days + 1
        b = max(0, delta)
        overlap.append(b)
        
    #mod_fd = df_merge_col.assign(overlap_days = overlap)
    #co = mod_fd[mod_fd.overlap_days != 0].reset_index()
    
    #newpt=(np.NaN,np.NaN)
    #event_pt=[]
    #nevent=0
    #for pt in zip(co['latitude'],co['longitude']):
        #if pt != newpt:
            #nevent=0
            #newpt=pt
        #else:
            #nevent=nevent+1
        #event_pt.append(nevent)
    #len(event_pt)
    
    #co['event']=event_pt
    #co.set_index(['event','latitude', 'longitude'], inplace=True)
    #ds=co.to_xarray()
    #ds.to_netcdf('co-events.nc')
    
    mod_fd = df_merge_col.assign(overlap_days = overlap)
    thw = mod_fd[mod_fd.overlap_days == 0].reset_index()
    
    newpt=(np.NaN,np.NaN)
    event_pt=[]
    nevent=0
    for pt in zip(thw['latitude'],thw['longitude']):
        if pt != newpt:
            nevent=0
            newpt=pt
        else:
            nevent=nevent+1
        event_pt.append(nevent)
    len(event_pt)
    
    thw['event']=event_pt
    thw.set_index(['event','latitude', 'longitude'], inplace=True)
    ds_thw=thw.to_xarray()
    ds_thw.to_netcdf('stand-alone-thw.nc')