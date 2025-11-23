import pandas as pd
import shutil

TPAR_FILE = "ahangama_boundary.bnd"
TPAR_COPY = "ahangama_boundary_copy.bnd" 
INPUT_FILE = "INPUT"
BATHY_FILE = "ahangama.bot"

XPC, YPC = 80.252083, 5.852083
XLEN, YLEN = 0.1458, 0.1458
MX, MY = 35, 35
DX, DY = 0.004167, 0.004167

def get_sim_times(tpar_file):
    try:
        # Read first and last line only to get range
        df = pd.read_csv(tpar_file, skiprows=1, delim_whitespace=True, header=None, dtype={0:str})
        start = str(df.iloc[0, 0])
        end = str(df.iloc[-1, 0])
        return start, end
    except:
        return "20250101.0000", "20250101.0300"

def main():
    try:
        shutil.copy(TPAR_FILE, TPAR_COPY)
    except: pass

    start_time, end_time = get_sim_times(TPAR_FILE)
    print(f"   Simulation Range: {start_time} -> {end_time}")

    swan_code = f"""$ SWAN INPUT: AHANGAMA (7 DAY / 3 HR)
PROJECT 'AHANGAMA' '1'
MODE NONSTATIONARY
COORDINATES SPHERICAL

$ 1. GRID
CGRID REGULAR {XPC} {YPC} 0.0 {XLEN} {YLEN} {MX} {MY} CIRCLE 36 0.05 1.0 24
INPGRID BOTTOM {XPC} {YPC} 0.0 {MX} {MY} {DX} {DY} EXC -99
READGRID BOTTOM 1 '{BATHY_FILE}' 1 0 FREE

$ 2. BOUNDARIES
BOUND SHAPE JONSWAP 3.3 PEAK DSPR DEGREES

$ SOUTH BOUNDARY (Primary Swell Source for South Coast)
BOUNDSPEC SIDE SOUTH CONSTANT FILE '{TPAR_FILE}'

$ WEST BOUNDARY (Secondary Source - replacing East!)
$ Ahangama is South-West coast, so energy comes from S and W.
BOUNDSPEC SIDE WEST CONSTANT FILE '{TPAR_COPY}'

$ 3. PHYSICS
BREAKING CON 1.0 0.73
FRICTION JONSWAP CONSTANT 0.067
OFF WCAP
OFF QUAD

$ 4. NUMERICS
PROP BSBT
NUMERIC STOPC 0.005 0.005 0.005 95. STAT 15

$ 5. OUTPUT POINTS (Updated for Ahangama Grid)
$ DEEP: Near the SW corner of your grid
POINTS 'DEEP' 80.2600 5.8600

$ MID: Halfway to the surf
POINTS 'MID'  80.3100 5.9100

$ SURF: Just offshore of Ahangama (5.970)
POINTS 'SURF' 80.3630 5.9650

$ OUTPUT TABLES
TABLE 'DEEP' HEAD 'deep_forecast.tbl' HS TPS DIR DEPTH QB OUTPUT {start_time} 3 HR
TABLE 'MID'  HEAD 'mid_forecast.tbl'  HS TPS DIR DEPTH QB OUTPUT {start_time} 3 HR
TABLE 'SURF' HEAD 'surf_forecast.tbl' HS TPS DIR DEPTH QB OUTPUT {start_time} 3 HR

$ 6. RUN
COMPUTE {start_time} 15 MIN {end_time}
STOP
"""
    with open(INPUT_FILE, "w") as f:
        f.write(swan_code)
    print(f" Updated INPUT file.")

if __name__ == "__main__":
    main()