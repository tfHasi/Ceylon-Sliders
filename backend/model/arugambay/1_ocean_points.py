import numpy as np
import pickle
import pandas as pd

DATA_PATH = "../preprocessed_multiyear.pkl"
META_PATH = "../model_metadata.pkl"
TARGET_LAT = 6.8399
TARGET_LON = 81.8396

def main():
    print(" INSPECTING OCEAN POINTS...")

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

    print(f"\n GRID VISUALIZATION ({len(lats)}x{len(lons)})")
    print("   X = Land (<0.01m),  . = Ocean (>0.01m)\n")

    header = "      "
    for lon in lons:
        header += f"{int(lon)%100:02d}.{int((lon*100)%100):02d} "
    print(header)

    valid_points = []

    for i, lat in enumerate(lats):
        row_str = f"{lat:5.2f} "

        for j, lon in enumerate(lons):
            val = shts_map_meters[i, j]

            if ocean_mask[i, j]:
                row_str += "  .   "
                dist = np.sqrt((lat - TARGET_LAT)**2 + (lon - TARGET_LON)**2)
                valid_points.append({
                    "lat": lat, "lon": lon, "val": val,
                    "dist": dist, "idx": (i, j)
                })
            else:
                row_str += "  X   "

        print(row_str)

    print("\n\n VALID OCEAN POINTS (In Meters)")
    print("-" * 65)
    print(f"{'Lat':<8} {'Lon':<8} {'Dist(deg)':<12} {'Height(m)':<12} {'Grid Idx':<10}")
    print("-" * 65)

    east_points = [p for p in valid_points if p['lon'] > 81.0]
    east_points.sort(key=lambda x: x['dist'])

    if not east_points:
        print(" NO POINTS FOUND EAST OF 81.0°!")
    else:
        for p in east_points[:10]:
            print(f"{p['lat']:<8.4f} {p['lon']:<8.4f} {p['dist']:<12.4f} {p['val']:<12.2f} {p['idx']}")
    print("-" * 65)

if __name__ == "__main__":
    main()