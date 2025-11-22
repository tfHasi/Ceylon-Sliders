import pandas as pd
import shutil
import os

# CONFIGURATION
TPAR_FILE = "arugam_boundary.bnd"
TPAR_COPY = "arugam_boundary_copy.bnd" # Hack for SWAN file locking
INPUT_FILE = "INPUT"
BATHY_FILE = "arugam.bot"

# Grid Config (From your bathymetry)
XPC, YPC = 81.702083, 6.702083
XLEN, YLEN = 0.2958, 0.2958
MX, MY = 71, 71
DX, DY = 0.004167, 0.004167

def get_simulation_times(tpar_file):
    try:
        df = pd.read_csv(tpar_file, skiprows=1, delim_whitespace=True, header=None)
        start_str = str(df.iloc[0, 0])
        end_str = str(df.iloc[-1, 0])
        
        # Fix time string format if needed (YYYYMMDD.HHMM)
        if len(start_str.split('.')[1]) == 2: start_str += "00" # 06 -> 0600
        if len(end_str.split('.')[1]) == 2: end_str += "00"
        
        return start_str, end_str
    except Exception as e:
        print(f" Error reading TPAR: {e}")
        exit(1)

def main():
    print("  CONFIGURING SWAN (FIXED SYNTAX)...")
    
    # 1. Create the file copy for the North boundary
    try:
        shutil.copy(TPAR_FILE, TPAR_COPY)
        print(f"   Created boundary copy: {TPAR_COPY}")
    except:
        print("   Warning: Could not copy boundary file.")

    # 2. Get Timing
    start_time, end_time = get_simulation_times(TPAR_FILE)
    print(f"   Time Range: {start_time} -> {end_time}")

    # 3. Define SWAN Script
    swan_code = f"""$ SWAN INPUT FILE: ARUGAM BAY (DYNAMIC FIX)
PROJECT 'ARUGAM_BAY' '1'
MODE NONSTATIONARY
COORDINATES SPHERICAL

$ 1. GRID
CGRID REGULAR {XPC} {YPC} 0.0 {XLEN} {YLEN} {MX} {MY} CIRCLE 36 0.05 1.0 24

$ 2. BATHYMETRY
INPGRID BOTTOM {XPC} {YPC} 0.0 {MX} {MY} {DX} {DY} EXC -99
READGRID BOTTOM 1 '{BATHY_FILE}' 1 0 FREE

$ 3. BOUNDARIES
BOUND SHAPE JONSWAP 3.3 PEAK DSPR DEGREES

$ East Boundary (Uses original file)
BOUNDSPEC SIDE EAST CONSTANT FILE '{TPAR_FILE}'

$ North Boundary (Uses COPY file to avoid 'File already opened' error)
BOUNDSPEC SIDE NORTH CONSTANT FILE '{TPAR_COPY}'

$ 4. PHYSICS (Zero Dissipation Mode)
$ Instead of 'OFF FRICTION', we set coefficient to 0.0
FRICTION JONSWAP CONSTANT 0.0
OFF BREAKING
OFF WCAP
OFF REFRACTION
OFF QUAD
$ Triads are off by default in Deep water mode, so we omit the command to avoid errors

$ 5. NUMERICS
PROP BSBT
NUMERIC STOPC 0.005 0.005 0.005 95. STAT 15

$ 6. OUTPUTS
POINTS 'DEEP' 81.9979 6.9438
POINTS 'MID'  81.9000 6.8400
POINTS 'SURF' 81.8450 6.8400

$ Output every 1 Hour
TABLE 'DEEP' HEAD 'deep_forecast.tbl' HS TPS DIR DEPTH QB OUTPUT {start_time} 1 HR
TABLE 'MID'  HEAD 'mid_forecast.tbl'  HS TPS DIR DEPTH QB OUTPUT {start_time} 1 HR
TABLE 'SURF' HEAD 'surf_forecast.tbl' HS TPS DIR DEPTH QB OUTPUT {start_time} 1 HR

$ 7. RUN
COMPUTE {start_time} 15 MIN {end_time}
STOP
"""

    with open(INPUT_FILE, "w") as f:
        f.write(swan_code)

    print(f" Updated '{INPUT_FILE}' successfully.")

if __name__ == "__main__":
    main()