import xarray as xr
import pandas as pd
import numpy as np
import glob
import os

DATA_DIR = "../" 
OUTPUT_CSV = "ahangama_virtual_bouy_data.csv"
TARGET_LAT = 6.0
TARGET_LON = 80.0

def main():
    print(f" BUILDING HISTORY FROM NC FILES ({TARGET_LAT}, {TARGET_LON})...")
    
    files = sorted(glob.glob(os.path.join(DATA_DIR, "surf_data_*.nc")))
    if not files:
        print(" No .nc files found!")
        return

    all_dfs = []

    for f in files:
        print(f"   Processing {os.path.basename(f)}...")
        try:
            ds = xr.open_dataset(f)
            
            if 'expver' in ds.coords:
                try:
                    ds = ds.sel(expver=1).combine_first(ds.sel(expver=5))
                except:
                    pass

            point_ds = ds.sel(latitude=TARGET_LAT, longitude=TARGET_LON, method='nearest')
            df = point_ds.to_dataframe().reset_index()
            
            target_cols = ['valid_time', 'u10', 'v10', 'msl', 'shts', 'mpts', 'mdts']
            existing_cols = [c for c in target_cols if c in df.columns]
            
            df = df[existing_cols].rename(columns={'valid_time': 'time'})
            all_dfs.append(df)
            ds.close()
            
        except Exception as e:
            print(f" Error reading {f}: {e}")

    if all_dfs:
        final_df = pd.concat(all_dfs).sort_values('time').reset_index(drop=True)
        final_df = final_df.drop_duplicates(subset=['time'])
        
        final_df = final_df.interpolate(method='linear', limit_direction='both')
        
        final_df.to_csv(OUTPUT_CSV, index=False)
        print(f" History Built: {len(final_df)} rows. Range: {final_df['time'].iloc[0]} -> {final_df['time'].iloc[-1]}")
    else:
        print(" Failed to build history.")

if __name__ == "__main__":
    main()