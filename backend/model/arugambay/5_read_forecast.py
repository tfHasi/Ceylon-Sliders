import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta

BOUNDARY_FILE = "arugam_boundary.bnd"
SWAN_OUTPUT   = "surf_forecast.tbl"
START_TIME    = datetime(2025, 1, 1, 6, 0) # Must match your simulation start

# ARUGAM BAY CALIBRATION 
# Logic: We trust the Deep Water Energy (Boundary) more than the SWAN Grid Height
# but we trust SWAN for Refraction (Dir) and Period (Tp).
# Factor: 0.95 (Refraction Loss) * 1.3 (Shoaling Gain)
SURF_FACTOR = 0.95 * 1.3 

def load_boundary_data():
    """Reads the Input Swell Energy (Deep Water)"""
    if not os.path.exists(BOUNDARY_FILE):
        return None
    try:
        # TPAR Format: Time Hs Tp Dir Spread
        df = pd.read_csv(BOUNDARY_FILE, skiprows=1, delim_whitespace=True, header=None)
        df.columns = ["Time", "Deep_Hs", "Deep_Tp", "Deep_Dir", "Spread"]
        return df
    except Exception as e:
        print(f"Error reading Boundary file: {e}")
        return None

def load_swan_data():
    """Reads the Local Physics (Refraction/Shoaling)"""
    if not os.path.exists(SWAN_OUTPUT):
        return None
    try:
        cols = ["Hs", "Tp", "Dir", "Depth", "QB"]
        # SWAN tables usually have 7 header lines
        df = pd.read_csv(SWAN_OUTPUT, skiprows=7, delim_whitespace=True, names=cols)
        return df
    except Exception as e:
        print(f"Error reading SWAN output: {e}")
        return None

def get_surf_quality(face_height_ft):
    if face_height_ft < 1.0: return "FLAT"
    if face_height_ft < 3.0: return "POOR"
    if face_height_ft < 5.0: return "FAIR"
    if face_height_ft < 8.0: return "GOOD"
    return "EPIC"

def main():
    print("\nARUGAM BAY SURF FORECAST (HYBRID CALIBRATION)")
    print("=" * 80)

    # 1. Load Data
    df_bnd = load_boundary_data()
    df_swan = load_swan_data()

    # 2. Validation
    if df_bnd is None or df_swan is None:
        print("Critical Error: Missing input files.")
        return

    # Ensure we don't crash if file lengths differ (take the shortest common length)
    steps = min(len(df_bnd), len(df_swan))
    
    if steps == 0:
        print("Error: Files are empty.")
        return

    print(f"Processing {steps} forecast steps...\n")

    # 3. Create Combined Dataframe
    results = []
    
    for i in range(steps):
        # Extract Raw Data
        deep_hs = df_bnd.iloc[i]['Deep_Hs']
        
        # Local Physics from SWAN
        local_tp = df_swan.iloc[i]['Tp']
        local_dir = df_swan.iloc[i]['Dir']
        swan_raw_hs = df_swan.iloc[i]['Hs'] # For engineering comparison only
        
        # --- THE CALIBRATION FORMULA ---
        # We apply the factor to the DEEP water energy, ignoring SWAN's height loss
        surf_hs_m = deep_hs * SURF_FACTOR
        surf_hs_ft = surf_hs_m * 3.28084
        
        # Timestamp
        step_time = START_TIME + timedelta(hours=i*6) # Assuming 6hr steps based on your other scripts
        
        results.append({
            "time": step_time,
            "deep_hs": deep_hs,
            "swan_hs": swan_raw_hs,
            "surf_ft": surf_hs_ft,
            "tp": local_tp,
            "dir": local_dir,
            "quality": get_surf_quality(surf_hs_ft)
        })

    df_res = pd.DataFrame(results)

    # PART 1: EXECUTIVE SUMMARY (PEAK EVENT)
    peak_idx = df_res['surf_ft'].idxmax()
    peak = df_res.iloc[peak_idx]

    print(f"{'METRIC':<25} {'VALUE':<25}")
    print("-" * 50)
    print(f"{'Best Time':<25} {peak['time'].strftime('%d-%b %I:%M %p')}")
    print(f"{'Offshore Swell':<25} {peak['deep_hs']:.2f} m")
    print(f"{'Swell Period':<25} {peak['tp']:.1f} s")
    print(f"{'Swell Direction':<25} {peak['dir']:.0f}°")
    print("-" * 50)
    print(f"{'PREDICTED FACE':<25} {peak['surf_ft']:.1f} - {peak['surf_ft']+1.5:.1f} ft")
    print(f"{'CONDITION':<25} {peak['quality']}")
    print("=" * 80)

    # PART 2: ENGINEERING NOTE
    print("\nENGINEERING CALIBRATION:")
    print(f"   Model Raw Output (Grid): {peak['swan_hs']:.2f}m")
    print(f"   Boundary Input (Deep):   {peak['deep_hs']:.2f}m")
    print(f"   Factor Applied:          {SURF_FACTOR:.3f}x")
    print(f"   Final Surf Height:       {peak['surf_ft']/3.28084:.2f}m ({peak['surf_ft']:.1f}ft)\n")

    # PART 3: DETAILED TIMELINE
    print("FORECAST TIMELINE")
    print("-" * 95)
    print(f"{'TIME':<15} {'DEEP Hs':<10} {'SWAN Hs':<10} {'SURF FACE':<20} {'DIR':<5} {'PER':<5} {'RATING'}")
    print("-" * 95)

    for _, row in df_res.iterrows():
        t_str = row['time'].strftime("%d-%b %H:%M")
        marker = " " if row['surf_ft'] != peak['surf_ft'] else "*"
        
        print(f"{t_str:<15} {row['deep_hs']:<6.2f}m    {row['swan_hs']:<6.2f}m    {marker} {row['surf_ft']:<4.1f} ft ({row['surf_ft']/3.28:.1f}m)    {row['dir']:<5.0f} {row['tp']:<5.1f} {row['quality']}")

    print("-" * 95)

if __name__ == "__main__":
    main()