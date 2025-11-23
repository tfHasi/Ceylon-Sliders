import pandas as pd
import numpy as np
import requests
import sys
import time
from datetime import datetime

HISTORY_CSV = "ahangama_virtual_bouy_data.csv"
TARGET_LAT = 6.0
TARGET_LON = 80.0

def main():
    url = "https://marine-api.open-meteo.com/v1/marine"
    params = {
        "latitude": TARGET_LAT,
        "longitude": TARGET_LON,
        "hourly": "wave_height,swell_wave_period,swell_wave_direction",
        "past_days": 5,
        "forecast_days": 8,
        "timezone": "UTC"
    }
    try:
        r = requests.get(url, params=params, timeout=10)
        data = r.json()
        if "error" in data and data["error"]:
            sys.exit(1)     
        if "hourly" not in data:
            sys.exit(1)
        df_live = pd.DataFrame(data['hourly'])
        df_live['time'] = pd.to_datetime(df_live['time'])
        df_live = df_live.rename(columns={
            'wave_height': 'shts',
            'swell_wave_period': 'mpts',
            'swell_wave_direction': 'mdts'
        })
        df_live['u10'] = 0.0
        df_live['v10'] = 0.0
        df_live['msl'] = 0.0
        df_live = df_live[['time', 'u10', 'v10', 'msl', 'shts', 'mpts', 'mdts']]
        
        try:
            df_hist = pd.read_csv(HISTORY_CSV)
            df_hist['time'] = pd.to_datetime(df_hist['time'])
            last_hist = df_hist['time'].iloc[-1]
            df_new = df_live[df_live['time'] > last_hist]
            
            if df_new.empty:
                print(f"   No new data found (Latest data: {df_live['time'].iloc[-1]}).")
                full_df = df_hist
            else:
                print(f"   Appending {len(df_new)} new rows...")
                full_df = pd.concat([df_hist, df_new]).sort_values('time').reset_index(drop=True)
                full_df.to_csv(HISTORY_CSV, index=False)
                print(f" Forecast Updated. CSV now ends at: {full_df['time'].iloc[-1]}")
                
        except FileNotFoundError:
            print(" History file missing.")
            df_live.to_csv(HISTORY_CSV, index=False)

    except Exception as e:
        print(f" Critical Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()