import openmeteo_requests
import requests_cache
import pandas as pd
import numpy as np
import pickle
from retry_requests import retry
from datetime import datetime, timedelta

META_PATH = "../model_metadata.pkl"
OUTPUT_LIVE_FILE = "live_input.pkl"

# The exact feature order your model was trained on
# [0:u10, 1:v10, 2:msl, 3:shts, 4:mpts, 5:mdts]
FEATURE_ORDER = ["u10", "v10", "msl", "shts", "mpts", "mdts"]

def get_open_meteo_client():
    cache_session = requests_cache.CachedSession('.cache', expire_after=3600)
    retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
    return openmeteo_requests.Client(session=retry_session)

def main():
    print(" FETCHING LIVE DATA...")

    # 1. Load Metadata
    with open(META_PATH, "rb") as f:
        meta = pickle.load(f)
    
    lats = meta['latitude']
    lons = meta['longitude']
    scalers_X = meta['scalers_X']

    print(f"   Grid Target: {len(lats)}x{len(lons)} points")

    # 2. Prepare Grid Points
    lat_mesh, lon_mesh = np.meshgrid(lats, lons, indexing='ij')
    lat_flat = lat_mesh.flatten()
    lon_flat = lon_mesh.flatten()

    # --- BATCHING LOGIC STARTS HERE ---
    client = get_open_meteo_client()
    
    # We will collect all responses here to mimic a single large request
    responses_marine = []
    responses_weather = []

    # API Endpoints
    url_marine = "https://marine-api.open-meteo.com/v1/marine"
    url_weather = "https://api.open-meteo.com/v1/forecast"

    # Define Batch Size (Open-Meteo handles ~50-100 locations comfortably in a GET URL)
    BATCH_SIZE = 50 
    total_points = len(lat_flat)

    print(f"   Requesting data in batches of {BATCH_SIZE}...")

    for i in range(0, total_points, BATCH_SIZE):
        # Slice the coordinates for this batch
        batch_lats = list(lat_flat[i : i + BATCH_SIZE])
        batch_lons = list(lon_flat[i : i + BATCH_SIZE])

        # Params for this specific batch
        params_marine = {
            "latitude": batch_lats,
            "longitude": batch_lons,
            "hourly": ["wave_height", "wave_period", "wave_direction", "wind_wave_height"],
            "past_days": 7,
            "timezone": "UTC"
        }

        params_weather = {
            "latitude": batch_lats,
            "longitude": batch_lons,
            "hourly": ["pressure_msl", "wind_speed_10m", "wind_direction_10m"],
            "past_days": 7,
            "timezone": "UTC"
        }

        # Fetch and Extend the main list
        # We use .extend() so the list grows: [Batch1_Data, Batch2_Data, ...]
        try:
            r_marine = client.weather_api(url_marine, params=params_marine)
            responses_marine.extend(r_marine)

            r_weather = client.weather_api(url_weather, params=params_weather)
            responses_weather.extend(r_weather)
            
            print(f"     Fetched batch {i} to {i+len(batch_lats)} successfully.")
            
        except Exception as e:
            print(f"     Error fetching batch starting at index {i}: {e}")
            return # Stop execution if a batch fails

    # --- BATCHING LOGIC ENDS HERE ---
    # The rest of your code works exactly as before because responses_marine 
    # now contains the data for all 441 points.

    # 3. Process & Grid the Data
    # Verify we have data for all points
    n_points = len(lat_flat)
    if len(responses_marine) != n_points:
        print(f"Error: Expected {n_points} responses, got {len(responses_marine)}")
        return

    # Check time length from first response
    n_hours = len(responses_marine[0].Hourly().Variables(0).ValuesAsNumpy())
    
    # Arrays to hold flattened spatial data (Time, Points)
    raw_u10 = np.zeros((n_hours, n_points))
    raw_v10 = np.zeros((n_hours, n_points))
    raw_msl = np.zeros((n_hours, n_points))
    raw_shts = np.zeros((n_hours, n_points))
    raw_mpts = np.zeros((n_hours, n_points))
    raw_mdts = np.zeros((n_hours, n_points))

    for i in range(n_points):
        # --- Weather Data ---
        w_data = responses_weather[i]
        ws = w_data.Hourly().Variables(1).ValuesAsNumpy() # Speed
        wd = w_data.Hourly().Variables(2).ValuesAsNumpy() # Direction
        msl = w_data.Hourly().Variables(0).ValuesAsNumpy()
        
        # Convert Speed/Dir to U/V
        wd_rad = np.radians(wd)
        raw_u10[:, i] = -ws * np.sin(wd_rad)
        raw_v10[:, i] = -ws * np.cos(wd_rad)
        raw_msl[:, i] = msl

        # --- Marine Data ---
        m_data = responses_marine[i]
        raw_shts[:, i] = m_data.Hourly().Variables(0).ValuesAsNumpy() # Sig Height
        raw_mpts[:, i] = m_data.Hourly().Variables(1).ValuesAsNumpy() # Period
        raw_mdts[:, i] = m_data.Hourly().Variables(2).ValuesAsNumpy() # Direction

    # 4. Reshape to (Time, Lat, Lon)
    def reshape_grid(flat_arr):
        return flat_arr.reshape(n_hours, len(lats), len(lons))

    grid_u10 = reshape_grid(raw_u10)
    grid_v10 = reshape_grid(raw_v10)
    grid_msl = reshape_grid(raw_msl)
    grid_shts = reshape_grid(raw_shts)
    grid_mpts = reshape_grid(raw_mpts)
    grid_mdts = reshape_grid(raw_mdts)

    # 5. Temporal Filtering (6-Hour Steps)
    indices = np.arange(0, n_hours, 6)
    
    X_combined = np.stack([
        grid_u10[indices], grid_v10[indices], grid_msl[indices],
        grid_shts[indices], grid_mpts[indices], grid_mdts[indices]
    ], axis=-1)

    # 6. Select Last 19 Steps
    if len(X_combined) < 19:
        raise ValueError("Not enough history fetched to create a sequence!")
    
    X_final_seq = X_combined[-19:] 
    print(f"   Raw Sequence Shape: {X_final_seq.shape}")

    # 7. Scale
    X_scaled = np.zeros_like(X_final_seq)
    for i in range(6):
        # print(f"   Scaling channel {i} ({FEATURE_ORDER[i]})...") # Optional print
        scaler = scalers_X[i]
        flat_chan = X_final_seq[..., i].reshape(-1, 1)
        scaled_chan = scaler.transform(flat_chan).reshape(X_final_seq[..., i].shape)
        X_scaled[..., i] = scaled_chan

    # 8. Save
    final_input = np.expand_dims(X_scaled, axis=0)
    last_ts = datetime.utcnow()
    
    data_packet = {
        "X_live": final_input,
        "last_timestamp": last_ts 
    }

    with open(OUTPUT_LIVE_FILE, "wb") as f:
        pickle.dump(data_packet, f)

    print(f" Saved {OUTPUT_LIVE_FILE}. Ready for forecasting.")
    
if __name__ == "__main__":
    main()