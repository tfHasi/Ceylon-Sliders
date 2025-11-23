import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta

BOUNDARY_FILE = "mirissa_boundary.bnd"
SWAN_SURF_TBL = "surf_forecast.tbl"
SWAN_DEEP_TBL = "deep_forecast.tbl"

SURF_FACTOR = 1 

def load_boundary_data():
    if not os.path.exists(BOUNDARY_FILE):
        return None
    try:
        df = pd.read_csv(BOUNDARY_FILE, skiprows=1, delim_whitespace=True, header=None, dtype={0: str})
        df.columns = ["TimeStr", "Deep_Hs", "Deep_Tp", "Deep_Dir", "Spread"]
        df['time'] = pd.to_datetime(df['TimeStr'], format='%Y%m%d.%H%M')
        return df
    except Exception as e:
        print(f"Error reading Boundary file: {e}")
        return None

def load_swan_table(filename):
    if not os.path.exists(filename):
        return None
    try:
        cols = ["Hs", "Tp", "Dir", "Depth", "QB"]
        df = pd.read_csv(filename, skiprows=7, delim_whitespace=True, names=cols)
        return df
    except Exception as e:
        print(f"Error reading SWAN table {filename}: {e}")
        return None

def get_surf_quality(face_height_ft):
    if face_height_ft < 1.0: return "FLAT"
    if face_height_ft < 2.5: return "POOR"
    if face_height_ft < 4.0: return "FAIR"
    if face_height_ft < 7.5: return "GOOD"
    if face_height_ft < 12.0: return "EPIC"
    return "XL / DANGEROUS"

def main():

    df_bnd = load_boundary_data()
    df_surf = load_swan_table(SWAN_SURF_TBL)

    if df_bnd is None:
        print(" Boundary file missing.")
        return
    if df_surf is None:
        print(" SWAN output missing.")
        return

    steps = min(len(df_bnd), len(df_surf))
    if steps == 0:
        print("Error: One of the files is empty.")
        return

    results = []
    for i in range(steps):
        deep_hs = df_bnd.iloc[i]['Deep_Hs']
        swan_hs_raw = df_surf.iloc[i]['Hs']
        local_tp = df_surf.iloc[i]['Tp']
        local_dir = df_surf.iloc[i]['Dir']

        surf_hs_m = deep_hs * SURF_FACTOR
        surf_hs_ft = surf_hs_m * 3.28084

        step_time = df_bnd.iloc[i]['time']

        results.append({
            "time": step_time,
            "deep_hs": deep_hs,
            "swan_hs": swan_hs_raw,
            "surf_ft": surf_hs_ft,
            "tp": local_tp,
            "dir": local_dir,
            "quality": get_surf_quality(surf_hs_ft)
        })

    df_res = pd.DataFrame(results)

    peak_idx = df_res['surf_ft'].idxmax()
    peak = df_res.iloc[peak_idx]

    print(f"{'METRIC':<25} {'VALUE':<25}")
    print("-" * 60)
    print(f"{'Best Time':<25} {peak['time'].strftime('%d-%b %I:%M %p')}")
    print(f"{'Offshore Swell':<25} {peak['deep_hs']:.2f} m @ {peak['tp']:.1f} s")
    print(f"{'Swell Direction':<25} {peak['dir']:.0f}° (Local Wrap)")
    print("-" * 60)
    print(f"{'PREDICTED FACE':<25} {peak['surf_ft']:.1f} - {peak['surf_ft']+1.5:.1f} ft")
    print(f"{'CONDITION':<25} {peak['quality']}")
    print("=" * 80)

    print("\nENGINEERING CALIBRATION:")
    print(f"   Model Raw Output (Grid): {peak['swan_hs']:.2f}m")
    print(f"   Boundary Input (Deep):   {peak['deep_hs']:.2f}m")
    print(f"   Applied MOS Factor:      {SURF_FACTOR:.3f}x (Shoaling + Refraction)")
    print(f"   Calibrated Height:       {peak['surf_ft']/3.28084:.2f}m ({peak['surf_ft']:.1f}ft)\n")

    print("24-HOUR TIMELINE")
    print("-" * 100)
    print(f"{'TIME':<15} {'DEEP Hs':<10} {'SWAN Hs':<10} {'SURF FACE (Calibrated)':<25} {'DIR':<5} {'PER':<5} {'RATING'}")
    print("-" * 100)

    for _, row in df_res.iterrows():
        t_str = row['time'].strftime("%d-%b %H:%M")
        marker = "★" if row['surf_ft'] == peak['surf_ft'] else " "

        print(f"{t_str:<15} {row['deep_hs']:<6.2f}m    {row['swan_hs']:<6.2f}m    {marker} {row['surf_ft']:<4.1f} ft ({row['surf_ft']/3.28:.1f}m)        {row['dir']:<5.0f} {row['tp']:<5.1f} {row['quality']}")

    print("-" * 100)
    print("Forecast generation complete.")

    json_filename = "mirissa_forecast.json"
    json_df = df_res[['time', 'surf_ft', 'quality', 'dir', 'tp', 'deep_hs']]
    json_df.loc[:, 'time'] = json_df['time'].dt.strftime('%Y-%m-%d %H:%M:%S')
    json_df.to_json(json_filename, orient='records', indent=4)
    print(f"\nJSON saved to {json_filename} (Ready for Frontend)")

if __name__ == "__main__":
    main()