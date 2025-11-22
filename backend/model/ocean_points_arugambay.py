import numpy as np
import pickle
import pandas as pd

# CONFIG
DATA_PATH = "preprocessed_multiyear.pkl"
META_PATH = "model_metadata.pkl"
TARGET_LAT = 6.8399  # Arugam Bay
TARGET_LON = 81.8396

def main():
    print("🔍 INSPECTING MODEL'S OCEAN MASK (FIXED)...")
    
    # 1. Load Data
    with open(DATA_PATH, "rb") as f:
        data = pickle.load(f)
    with open(META_PATH, "rb") as f:
        meta = pickle.load(f)

    # Get the LAST sequence
    # Shape: (1, 19, 21, 21, 6)
    last_seq = data['X_val'][-1:]
    
    # Extract Coordinates
    lats = meta['latitude']
    lons = meta['longitude']
    
    # 2. Create the Mask (CORRECTED SLICING)
    # shape[0] is batch (1), slice [0] to remove it -> (19, 21, 21, 6)
    # [:, :, :, 3] selects All Times, All Lats, All Lons, Channel 3 ('shts')
    shts_data = last_seq[0, :, :, :, 3] 
    
    # Average over time to get the 2D Map
    shts_map = np.mean(shts_data, axis=0)
    
    print(f"   Map Shape: {shts_map.shape} (Should be 21, 21)")
    
    # 3. Print the "ASCII Map"
    print(f"\n🗺️  GRID VISUALIZATION ({len(lats)}x{len(lons)})")
    print("   X = Land (0.0),  . = Ocean (>0.0)\n")
    
    # Print Longitude Headers
    header = "      "
    for lon in lons:
        header += f"{int(lon)%100:02d}.{int((lon*100)%100):02d} "
    print(header)

    valid_points = []

    for i, lat in enumerate(lats):
        row_str = f"{lat:5.2f} " 
        
        for j, lon in enumerate(lons):
            val = shts_map[i, j]
            
            # Check if it is Ocean (approx > 0)
            if abs(val) > 1e-5: 
                row_str += "  .   "
                
                dist = np.sqrt((lat - TARGET_LAT)**2 + (lon - TARGET_LON)**2)
                valid_points.append({
                    "lat": lat, "lon": lon, "val": val, 
                    "dist": dist, "idx": (i, j)
                })
            else:
                row_str += "  X   "
        
        print(row_str)

    # 4. Print Valid East Coast Points
    print("\n\n📋 LIST OF VALID OCEAN POINTS (East of 81.0°)")
    print("-" * 65)
    print(f"{'Lat':<8} {'Lon':<8} {'Dist(deg)':<12} {'Raw Value':<12} {'Grid Idx':<10}")
    print("-" * 65)

    east_points = [p for p in valid_points if p['lon'] > 81.0]
    east_points.sort(key=lambda x: x['dist'])

    if not east_points:
        print("⚠️  NO POINTS FOUND EAST OF 81.0°!")
    else:
        for p in east_points[:10]:
            print(f"{p['lat']:<8.4f} {p['lon']:<8.4f} {p['dist']:<12.4f} {p['val']:<12.4f} {p['idx']}")
    print("-" * 65)

if __name__ == "__main__":
    main()