import xarray as xr
import numpy as np
import os

# CONFIGURATION FOR AHANGAMA
INPUT_NC = "GEBCO_Ahangama.nc"
OUTPUT_BOT = "ahangama.bot"

def main():
    print(f" PROCESSING BATHYMETRY FOR AHANGAMA...")

    ds = xr.open_dataset(INPUT_NC)['elevation'].sortby('lat')
    lat, lon = ds.lat.values, ds.lon.values
    bathymetry = -ds.values
    bathymetry[bathymetry < 0] = -99
    np.savetxt(OUTPUT_BOT, bathymetry, fmt="%.2f")
    print(f" Saved {OUTPUT_BOT}")

    dx = abs(lon[1] - lon[0])
    dy = abs(lat[1] - lat[0])
    mx = len(lon) - 1
    my = len(lat) - 1
    x_len = lon[-1] - lon[0]
    y_len = lat[-1] - lat[0]
    
    print("-" * 70)
    print(f"XPC (Origin X) : {lon[0]:.6f}")
    print(f"YPC (Origin Y) : {lat[0]:.6f}")
    print(f"XLEN (Length X): {x_len:.4f}")
    print(f"YLEN (Length Y): {y_len:.4f}")
    print(f"MX (Cells X)   : {mx}")
    print(f"MY (Cells Y)   : {my}")
    print(f"DX (Res X)     : {dx:.6f}")
    print(f"DY (Res Y)     : {dy:.6f}")
    print("-" * 70)
    
    print(f"\nGenerated SWAN Command Preview:")
    print(f"CGRID REGULAR {lon[0]:.6f} {lat[0]:.6f} 0.0 {x_len:.4f} {y_len:.4f} {mx} {my}")
    print(f"INPGRID BOTTOM {lon[0]:.6f} {lat[0]:.6f} 0.0 {mx} {my} {dx:.6f} {dy:.6f} EXC -99")

if __name__ == "__main__":
    main()