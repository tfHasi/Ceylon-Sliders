import pandas as pd
import numpy as np
import requests
import sys
import time
from datetime import datetime

# CONFIGURATION
HISTORY_CSV = "arugambay_virtual_bouy_data.csv"
TARGET_LAT = 7.0
TARGET_LON = 82.0

def main():
    print("\n FETCHING LIVE FORECAST (WAVES ONLY)...")
    
    # 1. Define the Marine API
    url = "https://marine-api.open-meteo.com/v1/marine"
    
    # CORRECTED PARAMETERS: 
    # 'significant_wave_height' -> 'wave_height'
    params = {
        "latitude": TARGET_LAT,
        "longitude": TARGET_LON,
        "hourly": "wave_height,swell_wave_period,swell_wave_direction",
        "past_days": 5,
        "forecast_days": 3,
        "timezone": "UTC"
    }

    # 2. Fetch Data
    try:
        print(f"   Requesting Marine Data from {url}...")
        r = requests.get(url, params=params, timeout=10)
        data = r.json()
        
        # Error Checking
        if "error" in data and data["error"]:
            print(f" API returned error: {data['reason']}")
            sys.exit(1)
            
        if "hourly" not in data:
            print(f" Unexpected response format. Keys found: {data.keys()}")
            sys.exit(1)

        # 3. Process into DataFrame
        df_live = pd.DataFrame(data['hourly'])
        df_live['time'] = pd.to_datetime(df_live['time'])

        # 4. RENAME COLUMNS (Mapping API names to your Project names)
        # wave_height -> shts (Significant Height of Total Swell)
        df_live = df_live.rename(columns={
            'wave_height': 'shts',
            'swell_wave_period': 'mpts',
            'swell_wave_direction': 'mdts'
        })

        # 5. FILL MISSING COLUMNS (The Dummy Fill)
        # Your pipeline expects 7 columns (including wind), so we fill them with 0.
        df_live['u10'] = 0.0
        df_live['v10'] = 0.0
        df_live['msl'] = 0.0
        
        # Reorder to match history schema exactly
        df_live = df_live[['time', 'u10', 'v10', 'msl', 'shts', 'mpts', 'mdts']]

        # 6. Merge with History
        try:
            df_hist = pd.read_csv(HISTORY_CSV)
            df_hist['time'] = pd.to_datetime(df_hist['time'])
            
            last_hist = df_hist['time'].iloc[-1]
            
            # Keep only new data that comes after history
            df_new = df_live[df_live['time'] > last_hist]
            
            if df_new.empty:
                print(f"   No new data found (Latest API data: {df_live['time'].iloc[-1]}).")
                # Just rewrite history to ensure consistency
                full_df = df_hist
            else:
                print(f"   Appending {len(df_new)} new rows...")
                full_df = pd.concat([df_hist, df_new]).sort_values('time').reset_index(drop=True)
                full_df.to_csv(HISTORY_CSV, index=False)
                print(f" Forecast Updated. CSV now ends at: {full_df['time'].iloc[-1]}")
                
        except FileNotFoundError:
            print(" History file missing. Creating new one from Live Data.")
            df_live.to_csv(HISTORY_CSV, index=False)

    except Exception as e:
        print(f" Critical Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()