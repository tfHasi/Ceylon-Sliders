import xarray as xr
import numpy as np

INPUT_NC = "GEBCO_Arugambay.nc"
OUTPUT_BOT = "arugam.bot"

def main():
    print(f"  Processing {INPUT_NC}...")

    # 1. Load and Force South-to-North Orientation (Critical for SWAN)
    ds = xr.open_dataset(INPUT_NC)['elevation'].sortby('lat')
    lat, lon = ds.lat.values, ds.lon.values

    # 2. Convert Logic: GEBCO (Neg=Water) -> SWAN (Pos=Depth)
    # Any remaining negative values (originally Land) become -99
    bathymetry = -ds.values
    bathymetry[bathymetry < 0] = -99

    # 3. Save ASCII
    np.savetxt(OUTPUT_BOT, bathymetry, fmt="%.2f")
    print(f" Saved {OUTPUT_BOT}")

    # 4. Print Exact SWAN Configuration
    dx, dy = abs(lon[1] - lon[0]), abs(lat[1] - lat[0])
    mx, my = len(lon) - 1, len(lat) - 1
    
    print("-" * 70)
    print(f"CGRID REGULAR {lon[0]:.6f} {lat[0]:.6f} 0.0 {lon[-1]-lon[0]:.4f} {lat[-1]-lat[0]:.4f} {mx} {my}")
    print(f"INPGRID BOTTOM {lon[0]:.6f} {lat[0]:.6f} 0.0 {mx} {my} {dx:.6f} {dy:.6f} EXC -99")
    print("-" * 70)

if __name__ == "__main__":
    main()