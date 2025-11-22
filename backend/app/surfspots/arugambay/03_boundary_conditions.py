import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# CONFIGURATION
CSV_FILE = "arugambay_virtual_bouy_data.csv" 
OUTPUT_BND = "arugam_boundary.bnd"
FORECAST_HOURS = 24 

def main():
    print("\n GENERATING BOUNDARY FILE...")
    
    try:
        df = pd.read_csv(CSV_FILE)
        df['time'] = pd.to_datetime(df['time'])
    except:
        print(" Error loading CSV.")
        return

    # Define Window (Now -> Now+24h)
    now_time = datetime.utcnow()
    start_time = now_time.replace(minute=0, second=0, microsecond=0)
    end_time = start_time + timedelta(hours=FORECAST_HOURS)

    mask = (df['time'] >= start_time) & (df['time'] <= end_time)
    forecast_df = df.loc[mask]

    if forecast_df.empty:
        print(" CRITICAL: No future data in CSV. Check Script 2.")
        return

    # Write TPAR
    with open(OUTPUT_BND, "w") as f:
        f.write("TPAR\n")
        for _, row in forecast_df.iterrows():
            t_str = row['time'].strftime("%Y%m%d.%H%M")
            hs = max(0.01, row['shts']) # Safety clamp
            tp = max(1.0, row['mpts'])
            dr = row['mdts']
            
            f.write(f"{t_str} {hs:.2f} {tp:.2f} {dr:.1f} 30.0\n")

    print(f" Boundary File ({OUTPUT_BND}) Created. Steps: {len(forecast_df)}")

if __name__ == "__main__":
    main()