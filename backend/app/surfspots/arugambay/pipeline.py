import subprocess
import sys
import time
import os
from swan_helper import run_swan_in_wsl

def run_step(script):
    res = subprocess.run([sys.executable, script])
    if res.returncode != 0:
        print(f" STOPPED: Error in {script}")
        sys.exit(1)

def main():
    start = time.time()
    
    run_step("01_build_history.py")
    run_step("02_update_forecast.py")
    run_step("03_boundary_conditions.py")
    run_step("04_configure_swan.py")
    run_swan_in_wsl()
    
    subprocess.run([sys.executable, "05_read_forecast.py"])
    
    print(f"\n PIPELINE COMPLETE in {time.time() - start:.1f}s")

if __name__ == "__main__":
    main()