import pandas as pd
import shutil

TPAR_FILE = "arugam_boundary.bnd"
TPAR_COPY = "arugam_boundary_copy.bnd" 
INPUT_FILE = "INPUT"
BATHY_FILE = "arugam.bot"

XPC, YPC = 81.702083, 6.702083
XLEN, YLEN = 0.2958, 0.2958
MX, MY = 71, 71
DX, DY = 0.004167, 0.004167

def get_sim_times(tpar_file):
    try:
        df = pd.read_csv(tpar_file, skiprows=1, delim_whitespace=True, header=None)
        start = str(df.iloc[0, 0])
        end = str(df.iloc[-1, 0])
        if len(start.split('.')[1]) == 2: start += "00"
        if len(end.split('.')[1]) == 2: end += "00"
        return start, end
    except Exception as e:
        print(f"Error reading TPAR: {e}")
        return "Error" # Fallback

def main():
    try:
        shutil.copy(TPAR_FILE, TPAR_COPY)
    except: pass

    start_time, end_time = get_sim_times(TPAR_FILE)
    print(f"   Simulation Range: {start_time} -> {end_time}")

    swan_code = f"""$ SWAN INPUT: ARUGAM BAY (7 DAY / 3 HR)
PROJECT 'ARUGAM' '1'
MODE NONSTATIONARY
COORDINATES SPHERICAL

$ 1. GRID
CGRID REGULAR {XPC} {YPC} 0.0 {XLEN} {YLEN} {MX} {MY} CIRCLE 36 0.05 1.0 24
INPGRID BOTTOM {XPC} {YPC} 0.0 {MX} {MY} {DX} {DY} EXC -99
READGRID BOTTOM 1 '{BATHY_FILE}' 1 0 FREE

$ 2. BOUNDARIES
BOUND SHAPE JONSWAP 3.3 PEAK DSPR DEGREES
BOUNDSPEC SIDE EAST CONSTANT FILE '{TPAR_FILE}'
BOUNDSPEC SIDE SOUTH CONSTANT FILE '{TPAR_COPY}'

$ 3. PHYSICS
BREAKING CON 1.0 0.73
FRICTION JONSWAP CONSTANT 0.067
OFF WCAP
OFF QUAD

$ 4. NUMERICS
PROP BSBT
NUMERIC STOPC 0.005 0.005 0.005 95. STAT 15

$ 5. OUTPUT
POINTS 'DEEP' 81.9979 6.9438
POINTS 'MID'  81.9000 6.8400
POINTS 'SURF' 81.8450 6.8400

$ CHANGE: Output every 3 Hours now
TABLE 'DEEP' HEAD 'deep_forecast.tbl' HS TPS DIR DEPTH QB OUTPUT {start_time} 3 HR
TABLE 'MID'  HEAD 'mid_forecast.tbl'  HS TPS DIR DEPTH QB OUTPUT {start_time} 3 HR
TABLE 'SURF' HEAD 'surf_forecast.tbl' HS TPS DIR DEPTH QB OUTPUT {start_time} 3 HR

$ 6. RUN
COMPUTE {start_time} 15 MIN {end_time}
STOP
"""
    with open(INPUT_FILE, "w") as f:
        f.write(swan_code)
    print(f" Updated INPUT file successfully.")

if __name__ == "__main__":
    main()