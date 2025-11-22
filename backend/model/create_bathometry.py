import xarray as xr
import numpy as np

GEBCO_FILE = "GEBCO_Arugambay.nc" 
OUTPUT_FILE = "arugam.bot"

def main():
    print(f"🗺️  FIXING BATHYMETRY: {GEBCO_FILE}")
    
    ds = xr.open_dataset(GEBCO_FILE)
    elev = ds['elevation']
    
    # 1. Check Latitude Order
    lats = elev.lat.values
    lons = elev.lon.values
    
    print(f"   Original Latitudes: {lats[0]} to {lats[-1]}")
    
    # If data is North-to-South (descending), we must flip it for SWAN
    needs_flip = False
    if lats[0] > lats[-1]:
        print("   ⚠️  Data is Top-to-Bottom (North-to-South).")
        print("   🔄 Flipping array to match SWAN (South-to-North)...")
        elev = elev.isel(lat=slice(None, None, -1))
        lats = lats[::-1]
        needs_flip = True
    else:
        print("   ✅ Data is already South-to-North.")

    # 2. Extract Grid Parameters (Now Corrected)
    dx = np.abs(lons[1] - lons[0])
    dy = np.abs(lats[1] - lats[0])
    xpc = lons[0]
    ypc = lats[0] # This is now the Bottom-Left Corner
    mx = len(lons) - 1
    my = len(lats) - 1

    print("\n📋 COPY THIS TO INPUT FILE (SECTION 2 & 3):")
    print("-" * 50)
    print(f"CGRID REGULAR {xpc:.6f} {ypc:.6f} 0.0 {lons[-1]-lons[0]:.4f} {lats[-1]-lats[0]:.4f} {mx} {my}")
    print(f"INPGRID BOTTOM {xpc:.6f} {ypc:.6f} 0.0 {mx} {my} {dx:.6f} {dy:.6f}")
    print("-" * 50)

    # 3. Process Depth
    # GEBCO: neg = water. SWAN: pos = water.
    bathymetry = -1 * elev.values
    
    # Set Land to -99
    bathymetry = np.where(bathymetry < 0, -99, bathymetry)

    # 4. Save
    print(f"\n💾 Saving {OUTPUT_FILE}...")
    np.savetxt(OUTPUT_FILE, bathymetry, fmt="%.2f")
    print("✅ Done!")

if __name__ == "__main__":
    main()