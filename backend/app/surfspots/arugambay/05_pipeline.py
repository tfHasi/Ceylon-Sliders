import subprocess
import sys
import time
import os

def run_step(script):
    print(f"--------------------------------------------------")
    print(f"Running {script}...")
    # Use sys.executable to ensure we use the same python env
    res = subprocess.run([sys.executable, script])
    if res.returncode != 0:
        print(f" STOPPED: Error in {script}")
        sys.exit(1)

def main():
    start = time.time()
    
    # 1. Update Forecast (Open-Meteo -> CSV)
    run_step("02_update_forecast.py")
    
    # 2. Create Boundary (CSV -> .bnd)
    run_step("03_boundary_conditions.py")
    
    # 3. Configure SWAN (Update INPUT file)
    run_step("04_configure_swan.py")
    
    # --- THE MANUAL BRIDGE ---
    print("\n" + "="*50)
    print(" FILES PREPARED SUCCESSFULLY!")
    print("="*50)
    print(" ACTION REQUIRED:")
    print("1. Open  UBUNTU terminal.")
    print("2. Navigate to this folder.")
    print("3. Run this command:")
    print("\n    ./swan.exe \n")
    print("="*50)
    
    try:
        input("4. Press [ENTER] here once SWAN finishes... ")
    except KeyboardInterrupt:
        print("\nExiting.")
        sys.exit(0)

    # 4. Generate Report (Reads the .tbl files SWAN just made)
    print(f"--------------------------------------------------")
    print(" GENERATING FINAL REPORT...")
    subprocess.run([sys.executable, "06_read_forecast.py"])
    
    print(f"\n PIPELINE COMPLETE in {time.time() - start:.1f}s")

if __name__ == "__main__":
    main()