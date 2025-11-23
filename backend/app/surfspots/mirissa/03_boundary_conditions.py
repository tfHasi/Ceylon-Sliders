import pandas as pd
import numpy as np
from datetime import datetime, timedelta

CSV_FILE = "mirissa_virtual_bouy_data.csv" 
OUTPUT_BND = "mirissa_boundary.bnd"
FORECAST_HOURS = 168  # 7 days

def main():   
    try:
        df = pd.read_csv(CSV_FILE)
        df['time'] = pd.to_datetime(df['time'])
    except:
        print(" Error loading CSV.")
        return

    now_time = datetime.utcnow()
    current_hour = now_time.hour
    start_hour = (current_hour // 3) * 3
    start_time = now_time.replace(hour=start_hour, minute=0, second=0, microsecond=0)
    
    end_time = start_time + timedelta(hours=FORECAST_HOURS)

    mask = (df['time'] >= start_time) & (df['time'] <= end_time)
    forecast_df = df.loc[mask].copy()

    if forecast_df.empty:
        print("No future data in CSV.")
        return
    forecast_df = forecast_df[forecast_df['time'].dt.hour % 3 == 0]

    # Write TPAR
    with open(OUTPUT_BND, "w") as f:
        f.write("TPAR\n")
        for _, row in forecast_df.iterrows():
            t_str = row['time'].strftime("%Y%m%d.%H%M")
            hs = max(0.01, row['shts'])
            tp = max(1.0, row['mpts'])
            dr = row['mdts']
            
            f.write(f"{t_str} {hs:.2f} {tp:.2f} {dr:.1f} 30.0\n")

if __name__ == "__main__":
    main()