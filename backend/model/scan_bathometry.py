import numpy as np

# Config matches your INPUT file
XPC = 81.702083
YPC = 6.702083
DX = 0.004167
DY = 0.004167

print("🗺️  SCANNING BATHYMETRY FOR DEEP WATER...")

try:
    # Load the bot file
    # It's a 2D array. We assume standard SWAN reading (Bottom-Left origin)
    depths = np.loadtxt("arugam.bot")
    
    # Check shape
    print(f"   Grid Shape: {depths.shape}")
    
    # Find the maximum depth
    max_depth = np.max(depths)
    
    # Find the indices (row, col) of the deepest point
    # Note: np.where returns arrays, we take the first occurrence
    indices = np.where(depths == max_depth)
    row_idx = indices[0][0] # Y index
    col_idx = indices[1][0] # X index
    
    # Calculate Real Coordinates
    # Lon = StartX + (Col * DX)
    # Lat = StartY + (Row * DY)
    best_lon = XPC + (col_idx * DX)
    best_lat = YPC + (row_idx * DY)
    
    print("-" * 40)
    print(f"   ✅ DEEPEST POINT FOUND: {max_depth:.2f} meters")
    print(f"   📍 Coordinates: {best_lon:.4f} E, {best_lat:.4f} N")
    print(f"   ❌ Current Point (81.95, 6.84) depth was likely ~3.8m")
    print("-" * 40)
    print("   👉 Update your INPUT file with these exact coordinates.")

except Exception as e:
    print(f"Error reading arugam.bot: {e}")