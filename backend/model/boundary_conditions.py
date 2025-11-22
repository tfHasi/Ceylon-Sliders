"""
Extract offshore boundary conditions from your ConvLSTM forecasts
for SWAN input at Arugam Bay
"""
import xarray as xr
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from tensorflow.keras.models import load_model
import pickle

# ============================================================
# CONFIGURATION
# ============================================================
ARUGAM_BAY_LAT = 6.8399
ARUGAM_BAY_LON = 81.8396

# Offshore boundary points (virtual buoys around Arugam Bay)
# These will be used as SWAN boundary conditions
BOUNDARY_POINTS = {
    'EAST': (7.0, 82.0),   # Eastern boundary (deep water)
    'SOUTH': (6.5, 81.5),  # Southern boundary
    'NORTH': (7.5, 81.5),  # Northern boundary
}

# Time configuration
FORECAST_START = datetime(2024, 12, 31, 18, 0)  # Last available time
FORECAST_HOURS = 24  # 24-hour forecast

# ============================================================
# LOAD MODEL & METADATA
# ============================================================
print("Loading ConvLSTM model and metadata...")
model = load_model("convlstm_final.keras")

with open("model_metadata.pkl", "rb") as f:
    metadata = pickle.load(f)

scalers_X = metadata['scalers_X']
scalers_y = metadata['scalers_y']
lats = metadata['latitude']
lons = metadata['longitude']
lookback_hours = metadata['lookback_hours']

print(f"✓ Model loaded. Grid: {len(lats)}x{len(lons)}")

# ============================================================
# LOAD LATEST DATA FOR INPUT SEQUENCE
# ============================================================
print("\nLoading latest input data...")
ds = xr.open_dataset("surf_data_2024.nc")

# Get last available timesteps for input sequence
latest_time = ds.valid_time[-1].values
print(f"Latest available time: {pd.to_datetime(latest_time)}")

# Extract last 'lookback_hours' timesteps
ds_recent = ds.isel(valid_time=slice(-lookback_hours, None))

# Engineer features (same as training)
INPUT_FEATURES = metadata['input_features']
X = ds_recent[INPUT_FEATURES].to_array(dim="channel").transpose(
    "valid_time", "latitude", "longitude", "channel"
).values

# Scale features
X_scaled = np.zeros_like(X)
for i in range(X.shape[-1]):
    channel = X[..., i].reshape(-1, 1)
    X_scaled[..., i] = scalers_X[i].transform(channel).reshape(X[..., i].shape)

# Add batch dimension
X_input = X_scaled[np.newaxis, ...]  # Shape: (1, lookback, lat, lon, channels)

print(f"Input sequence shape: {X_input.shape}")

# ============================================================
# GENERATE FORECAST
# ============================================================
print("\nGenerating forecast...")
forecast_scaled = model.predict(X_input, verbose=0)[0]  # Remove batch dim

# Inverse transform
forecast = np.zeros_like(forecast_scaled)
for i in range(forecast_scaled.shape[-1]):
    forecast[..., i] = scalers_y[i].inverse_transform(
        forecast_scaled[..., i].reshape(-1, 1)
    ).reshape(forecast_scaled[..., i].shape)

print(f"Forecast shape: {forecast.shape}")

# ============================================================
# EXTRACT BOUNDARY CONDITIONS
# ============================================================
def find_nearest_indices(lats, lons, target_lat, target_lon):
    """Find nearest grid point indices"""
    lat_idx = np.argmin(np.abs(lats - target_lat))
    lon_idx = np.argmin(np.abs(lons - target_lon))
    return lat_idx, lon_idx

print("\nExtracting boundary conditions...")

# Create boundary condition dataframe
boundary_data = []

for location, (lat, lon) in BOUNDARY_POINTS.items():
    lat_idx, lon_idx = find_nearest_indices(lats, lons, lat, lon)
    
    # Extract wave parameters at this location
    Hs = forecast[lat_idx, lon_idx, 0]  # Significant wave height (m)
    Tp = forecast[lat_idx, lon_idx, 1]  # Peak period (s)
    Dir = forecast[lat_idx, lon_idx, 2]  # Direction (degrees)
    
    # Calculate frequency from period
    freq = 1.0 / Tp if Tp > 0 else 0.1
    
    boundary_data.append({
        'location': location,
        'lat': lats[lat_idx],
        'lon': lons[lon_idx],
        'Hs': Hs,
        'Tp': Tp,
        'Dir': Dir,
        'freq': freq
    })
    
    print(f"  {location:6s}: ({lats[lat_idx]:.2f}°N, {lons[lon_idx]:.2f}°E) "
          f"Hs={Hs:.2f}m, Tp={Tp:.1f}s, Dir={Dir:.0f}°")

df_boundary = pd.DataFrame(boundary_data)

# ============================================================
# SAVE BOUNDARY CONDITIONS FOR SWAN
# ============================================================
# SWAN uses TPAR format (Hs, Tp, Dir, DD, frequency)
# DD = directional spreading (default ~30 degrees for swell)

output_file = "swan_boundary_conditions.tpar"

with open(output_file, 'w') as f:
    f.write("TPAR\n")
    
    # Use EAST boundary (most offshore) as primary
    primary = df_boundary[df_boundary['location'] == 'EAST'].iloc[0]
    
    # SWAN expects: time, Hs, period, direction, spreading
    # For simplicity, use stationary conditions (single timestep)
    time_str = FORECAST_START.strftime("%Y%m%d.%H%M%S")
    
    f.write(f"{time_str}  {primary['Hs']:.3f}  {primary['Tp']:.2f}  "
            f"{primary['Dir']:.1f}  30.0\n")

print(f"\n✓ Boundary conditions saved to {output_file}")

# Also save as CSV for reference
df_boundary.to_csv("boundary_conditions.csv", index=False)
print(f"✓ Reference data saved to boundary_conditions.csv")

# ============================================================
# GENERATE WIND INPUT FOR SWAN
# ============================================================
print("\nExtracting local wind conditions...")

# Get wind at Arugam Bay location
lat_idx, lon_idx = find_nearest_indices(lats, lons, ARUGAM_BAY_LAT, ARUGAM_BAY_LON)

# Get wind from last timestep of ERA5 data
u10 = ds_recent['u10'].isel(valid_time=-1, latitude=lat_idx, longitude=lon_idx).values
v10 = ds_recent['v10'].isel(valid_time=-1, latitude=lat_idx, longitude=lon_idx).values

# Calculate wind speed and direction
wind_speed = np.sqrt(u10**2 + v10**2)
wind_dir = (270 - np.degrees(np.arctan2(v10, u10))) % 360  # Convert to nautical convention

print(f"Local wind at Arugam Bay: {wind_speed:.1f} m/s from {wind_dir:.0f}°")

# Save wind file for SWAN
with open("swan_wind.txt", 'w') as f:
    f.write(f"{wind_speed:.2f}  {wind_dir:.1f}\n")

print("✓ Wind conditions saved to swan_wind.txt")

# ============================================================
# SUMMARY
# ============================================================
print("\n" + "="*70)
print("BOUNDARY CONDITIONS EXTRACTED")
print("="*70)
print(f"Forecast time: {FORECAST_START}")
print(f"\nPrimary boundary (EAST):")
print(f"  Significant wave height: {primary['Hs']:.2f} m")
print(f"  Peak period: {primary['Tp']:.2f} s")
print(f"  Direction: {primary['Dir']:.0f}°")
print(f"\nLocal wind:")
print(f"  Speed: {wind_speed:.1f} m/s")
print(f"  Direction: {wind_dir:.0f}°")
print("="*70)
print("\n✓ Ready for SWAN! Next: Prepare bathymetry and run SWAN model")