import numpy as np
import pickle
import os

# Coordinates Hikkaduwa: 6.122241, 80.099103
TARGET_LAT = 6.12
TARGET_LON = 80.099

DATA_PATH = "../preprocessed_multiyear.pkl"
META_PATH = "../model_metadata.pkl"

def main():
    print(f" SEARCHING FOR VIRTUAL BUOY NEAR AHANGAMA ({TARGET_LAT}, {TARGET_LON})...")

    if not os.path.exists(DATA_PATH):
        print(f" Error: Could not find data at {DATA_PATH}")
        return

    with open(DATA_PATH, "rb") as f:
        data = pickle.load(f)
    with open(META_PATH, "rb") as f:
        meta = pickle.load(f)

    last_seq = data['X_val'][-1:]
    lats = meta['latitude']
    lons = meta['longitude']
    scaler_shts = meta['scalers_X'][3]

    shts_scaled = last_seq[0, :, :, :, 3]
    shts_map_scaled = np.mean(shts_scaled, axis=0)
    
    shape_2d = shts_map_scaled.shape
    shts_map_meters = scaler_shts.inverse_transform(
        shts_map_scaled.reshape(-1, 1)
    ).reshape(shape_2d)

    ocean_mask = shts_map_meters > 0.01

    print(f"\n GRID VISUALIZATION (South Coast Focus)")
    print("   X = Land,  . = Ocean")

    header = "      "
    for lon in lons:
        header += f"{lon:.2f} "
    print(header)

    valid_points = []

    for i, lat in enumerate(lats):
        row_str = f"{lat:5.2f} "
        for j, lon in enumerate(lons):
            val = shts_map_meters[i, j]

            if ocean_mask[i, j]:
                row_str += "  .   "
                
                # Calculate Euclidean Distance to Surf Spot
                dist = np.sqrt((lat - TARGET_LAT)**2 + (lon - TARGET_LON)**2)
                
                valid_points.append({
                    "lat": lat, "lon": lon, "val": val,
                    "dist": dist, "idx": (i, j)
                })
            else:
                row_str += "  X   "
        print(row_str)

    print("\n\n CANDIDATE VIRTUAL BUOYS (Sorted by Distance)")
    print("-" * 80)
    print(f"{'Lat':<8} {'Lon':<8} {'Dist(deg)':<12} {'Height(m)':<12} {'Grid Idx':<12}")
    print("-" * 80)

    valid_points.sort(key=lambda x: x['dist'])

    if not valid_points:
        print(" NO OCEAN POINTS FOUND! Check your Grid coordinates.")
    else:
        for p in valid_points[:5]:
            print(f"{p['lat']:<8.4f} {p['lon']:<8.4f} {p['dist']:<12.4f} {p['val']:<12.2f} {str(p['idx']):<12}")
            
    print("-" * 80)
    if valid_points:
        best = valid_points[0]
        print(f"\n RECOMMENDATION: Use Lat: {best['lat']}, Lon: {best['lon']}")

if __name__ == "__main__":
    main()