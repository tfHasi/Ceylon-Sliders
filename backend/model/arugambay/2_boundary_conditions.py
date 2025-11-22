import pickle
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from tensorflow.keras.models import load_model

MODEL_PATH = "../convlstm_final.keras"
META_PATH = "../model_metadata.pkl"
DATA_PATH = "../preprocessed_multiyear.pkl"
OUTPUT_FILE = "arugam_boundary.bnd"

BUOY_LAT_IDX = 8
BUOY_LON_IDX = 16

START_TIME = datetime(2025, 1, 1, 6, 0)
FORECAST_STEPS = 4

def main():
    print("GENERATING ITERATIVE FORECAST (24 Hours)...")

    model = load_model(MODEL_PATH)
    with open(META_PATH, "rb") as f:
        meta = pickle.load(f)
    with open(DATA_PATH, "rb") as f:
        data = pickle.load(f)

    current_seq = data['X_val'][-1:].copy()
    forecast_results = []

    print(f"Starting Inference Loop ({FORECAST_STEPS} steps)...")

    for step in range(FORECAST_STEPS):
        pred_waves = model.predict(current_seq, verbose=0)
        raw_point_data = pred_waves[0, BUOY_LAT_IDX, BUOY_LON_IDX, :]

        hs = meta['scalers_y'][0].inverse_transform([[raw_point_data[0]]])[0][0]
        tp = meta['scalers_y'][1].inverse_transform([[raw_point_data[1]]])[0][0]
        dr = meta['scalers_y'][2].inverse_transform([[raw_point_data[2]]])[0][0]

        forecast_results.append((hs, tp, dr))
        print(f"Step {step+1}: Hs={hs:.2f}m | Tp={tp:.2f}s | Dir={dr:.0f}°")

        last_frame = current_seq[:, -1, :, :, :]
        new_frame = last_frame.copy()
        new_frame[0, :, :, 3:] = pred_waves[0]
        new_frame = new_frame[:, np.newaxis, :, :, :]
        current_seq = np.concatenate([current_seq[:, 1:, ...], new_frame], axis=1)

    print(f"\nWriting {OUTPUT_FILE}...")
    with open(OUTPUT_FILE, "w") as f:
        f.write("TPAR\n")

        for i, (hs, tp, dr) in enumerate(forecast_results):
            t_str = (START_TIME + timedelta(hours=i*6)).strftime("%Y%m%d.%H%M")
            f.write(f"{t_str} {hs:.2f} {tp:.2f} {dr:.1f} 30.0\n")

        last_t_str = (START_TIME + timedelta(hours=FORECAST_STEPS*6)).strftime("%Y%m%d.%H%M")
        last_vals = forecast_results[-1]
        f.write(f"{last_t_str} {last_vals[0]:.2f} {last_vals[1]:.2f} {last_vals[2]:.1f} 30.0\n")

    print("Done.")

if __name__ == "__main__":
    main()