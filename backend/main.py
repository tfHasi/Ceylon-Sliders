import datetime
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.data_fetcher import RealTimeData
from model.arugambay.engine import ArugamBayEngine 

app = FastAPI()

# --- GLOBAL STATE ---
engines = {}
fetchers = {}

@app.on_event("startup")
async def startup_event():
    """Initialize Heavy Models on Startup"""
    print("🚀 Booting Surf Forecasting Engine...")
    
    # 1. Init Arugam Bay Engine
    arugam_dir = os.path.abspath(os.path.join("model", "arugambay"))
    engines['arugambay'] = ArugamBayEngine(arugam_dir)
    
    # 2. Init Data Fetcher (Shared)
    # Use scalers from the engine to configure the fetcher
    scalers = engines['arugambay'].meta['scalers_X']
    fetchers['arugambay'] = RealTimeData(scalers, cache_dir="cache")
    
    print("✅ System Ready.")

class UserRequest(BaseModel):
    experience: str
    concerns: str

@app.post("/forecast/{spot_id}")
async def get_forecast(spot_id: str, user: UserRequest):
    if spot_id not in engines:
        raise HTTPException(status_code=404, detail="Spot not found")
    
    engine = engines[spot_id]
    fetcher = fetchers[spot_id]
    
    try:
        input_seq = None
        last_ts = None
        
        # 1. Try to get Live Data
        nc_file = fetcher.fetch_recent_data()
        
        if nc_file:
            print("Using Live Data...")
            # IMPORTANT: Now expects a tuple (sequence, timestamp)
            input_seq, last_ts = fetcher.process_for_inference(nc_file)
            
            if input_seq is None:
                print("⚠️ Live Data Processing Failed.")
            else:
                print(f"✅ Live Data Ready. Ends at: {last_ts}")
        
        # 2. Fallback Logic
        if input_seq is None:
            print("⚠️ Falling back to Historical Data (Demo Mode).")
            input_seq = engine.data['X_val'][-1:]
            last_ts = None # No timestamp means no gap bridging needed

        # 3. Run Physics Engine
        # Pass last_ts so the engine knows if it needs to 'bridge the gap'
        metrics = engine.run_pipeline(input_seq, last_data_time=last_ts)
        
        if "error" in metrics:
            # If it's a hard error, we can decide to throw 500 or return partial data
            # For now, we raise error to see it in logs
            print(f"Engine Error: {metrics['error']}")
            raise HTTPException(status_code=500, detail=metrics['error'])

        # 4. Construct Response
        advice = f"Conditions are {metrics['quality']}. Expect {metrics['surf_min_ft']}-{metrics['surf_max_ft']}ft waves."
        if user.experience.lower() == "beginner" and metrics['surf_min_ft'] > 4:
            advice += " Caution: It might be too big for you today!"

        return {
            "spot": spot_id,
            "timestamp": str(datetime.utcnow()) if last_ts else "Historical Demo",
            "metrics": metrics,
            "advice": advice
        }

    except Exception as e:
        print(f"Pipeline Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))