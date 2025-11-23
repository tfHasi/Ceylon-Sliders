import pandas as pd
import numpy as np
import requests
import sys
import os
from datetime import datetime

HISTORY_CSV = "hikkaduwa_virtual_bouy_data.csv"
TARGET_LAT = 6.0
TARGET_LON = 80.0
URL = os.getenv("URL", "https://marine-api.open-meteo.com/v1/marine")

def get_climatology_means(df_hist, target_date):
    matches = df_hist[
        (df_hist['time'].dt.month == target_date.month) & 
        (df_hist['time'].dt.day == target_date.day) &
        (df_hist['time'].dt.hour == target_date.hour)
    ]
    
    if not matches.empty:
        return matches['u10'].mean(), matches['v10'].mean(), matches['msl'].mean()
    matches_daily = df_hist[
        (df_hist['time'].dt.month == target_date.month) & 
        (df_hist['time'].dt.day == target_date.day)
    ]
    
    if not matches_daily.empty:
        return matches_daily['u10'].mean(), matches_daily['v10'].mean(), matches_daily['msl'].mean()
    return df_hist['u10'].mean(), df_hist['v10'].mean(), df_hist['msl'].mean()

def main():
    params = {
        "latitude": TARGET_LAT,
        "longitude": TARGET_LON,
        "hourly": "wave_height,swell_wave_period,swell_wave_direction",
        "past_days": 5,
        "forecast_days": 8,
        "timezone": "UTC"
    }
    try:
        r = requests.get(URL, params=params, timeout=10)
        data = r.json() 
        if "error" in data and data["error"]:
            print(f" API Error: {data.get('reason', 'Unknown')}")
            sys.exit(1)     
        if "hourly" not in data:
            print(" Invalid API Response")
            sys.exit(1)
        df_live = pd.DataFrame(data['hourly'])
        df_live['time'] = pd.to_datetime(df_live['time'])
        df_live = df_live.rename(columns={
            'wave_height': 'shts',
            'swell_wave_period': 'mpts',
            'swell_wave_direction': 'mdts'
        })

        df_live = df_live[df_live['time'].dt.hour.isin([0, 6, 12, 18])].copy()
        print(f"   Downsampled to {len(df_live)} rows (6H intervals).")

        try:
            df_hist = pd.read_csv(HISTORY_CSV)
            df_hist['time'] = pd.to_datetime(df_hist['time'])
        except FileNotFoundError:
            print(" Critical: History file missing. Cannot perform Climatology Imputation.")
            sys.exit(1)

        print("   Imputing missing wind/pressure (Hour-Specific)...")
        
        u10_list, v10_list, msl_list = [], [], []
        
        for _, row in df_live.iterrows():
            u, v, msl = get_climatology_means(df_hist, row['time'])
            u10_list.append(u)
            v10_list.append(v)
            msl_list.append(msl)
            
        df_live['u10'] = u10_list
        df_live['v10'] = v10_list
        df_live['msl'] = msl_list
        
        df_live = df_live[['time', 'u10', 'v10', 'msl', 'shts', 'mpts', 'mdts']]
        last_hist_time = df_hist['time'].iloc[-1]
        df_new = df_live[df_live['time'] > last_hist_time]
        
        if df_new.empty:
            print(f" No new data found (History is up to date: {last_hist_time}).")
        else:
            print(f"   Appending {len(df_new)} new rows...")
            full_df = pd.concat([df_hist, df_new]).sort_values('time').reset_index(drop=True)
            full_df.to_csv(HISTORY_CSV, index=False)
            print(f" Forecast Updated. CSV now ends at: {full_df['time'].iloc[-1]}")

    except Exception as e:
        print(f" Critical Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()