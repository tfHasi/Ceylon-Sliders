import numpy as np
import pickle
import pandas as pd
from tensorflow.keras.models import load_model
from datetime import datetime, timedelta

MODEL_PATH = "convlstm_final.keras"
META_PATH = "model_metadata.pkl"
DATA_PATH = "preprocessed_multiyear.pkl"

# SWAN Output
TPAR_FILENAME = "arugam_boundary.bnd"
FORECAST_START_TIME = datetime(2025, 1, 1, 6, 0) 

# Location: 7.00°N, 82.00°E
# This point had a scaled value of 1.58 (Ocean) vs -0.47 (Land)
VIRTUAL_BUOY_IDX = (8, 16) 

def main():
    print("🌊 GENERATING SWAN BOUNDARY (FINAL MANUAL OVERRIDE)...")
    
    # 1. Load Assets
    print("   Loading model...")
    model = load_model(MODEL_PATH)
    
    with open(META_PATH, "rb") as f:
        meta = pickle.load(f)
    with open(DATA_PATH, "rb") as f:
        data = pickle.load(f)

    lats = meta['latitude']
    lons = meta['longitude']
    scalers_y = meta['scalers_y'] 
    
    # 2. Get Input Sequence
    # Using the last sequence from validation set
    last_sequence = data['X_val'][-1:] 
    
    # 3. Predict
    print(f"   Running Inference for fixed grid point {VIRTUAL_BUOY_IDX}...")
    forecast_scaled = model.predict(last_sequence, verbose=0)
    
    # 4. Extract Specific Point
    lat_idx, lon_idx = VIRTUAL_BUOY_IDX
    
    # Shape: (1, 21, 21, 3) -> Extract (1, 3)
    buoy_scaled = forecast_scaled[:, lat_idx, lon_idx, :]
    
    # 5. Inverse Transform (Unscale)
    buoy_final = []
    # 0: SHTS, 1: MPTS, 2: MDTS
    for i in range(3):
        val = scalers_y[i].inverse_transform(buoy_scaled[:, i].reshape(-1, 1))
        buoy_final.append(val[0][0])
        
    hs, tp, dir_deg = buoy_final
    
    # Coordinates for display
    # Note: 82.0E is 82.0, but let's use the actual array value
    actual_lat = lats[lat_idx]
    actual_lon = lons[lon_idx]

    print("-" * 50)
    print(f"📍 VIRTUAL BUOY REPORT")
    print(f"   Location:  {actual_lat:.2f}°N, {actual_lon:.2f}°E")
    print("-" * 50)
    print(f"   Swell Height (Hs): {hs:.2f} m")
    print(f"   Swell Period (Tp): {tp:.2f} s")
    print(f"   Direction (Dir):   {dir_deg:.1f} °")
    print("-" * 50)

    # 6. Sanity Check
    if hs <= 0.1:
        print("\n  WARNING: Wave height is near zero. Are you sure Index (8, 16) is correct?")
        print("    If this happens, try Index (6, 16) which had value 1.8039.")
    else:
        # 7. Write TPAR File
        print(f"   Writing {TPAR_FILENAME}...")
        with open(TPAR_FILENAME, "w") as f:
            f.write("TPAR\n")
            # Write 24h block
            for i in range(5):
                t = FORECAST_START_TIME + timedelta(hours=i*6)
                # SWAN expects: Time  Hs  Tp  Dir  DSPR
                # DSPR (Directional Spreading) = 30.0 is standard for swell
                line = f"{t.strftime('%Y%m%d.%H%M')} {hs:.2f} {tp:.2f} {dir_deg:.1f} 30.0\n"
                f.write(line)
                
        print("SUCCESS! Created boundary file for SWAN.")

if __name__ == "__main__":
    main()