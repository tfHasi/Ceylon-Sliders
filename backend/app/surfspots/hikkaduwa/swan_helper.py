import os
import subprocess
import sys

def run_swan_in_wsl():
    """
    Translates the current Windows path to a WSL path 
    and executes ./swan.exe inside the Ubuntu environment.
    """
    # 1. Get current Windows working directory
    cwd = os.getcwd()
    
    # 2. Convert C:\Path\To\File -> /mnt/c/Path/To/File
    # This handles the drive letter and direction of slashes
    drive, tail = os.path.splitdrive(cwd)
    drive_letter = drive[0].lower()
    wsl_path = f"/mnt/{drive_letter}{tail.replace(os.sep, '/')}"

    # 3. Construct the WSL command
    # wsl -e bash -c "cd 'path' && ./swan.exe"
    command = ["wsl", "bash", "-c", f"cd '{wsl_path}' && ./swan.exe"]

    try:
        # Run the command
        result = subprocess.run(command, check=True)
        print(" SWAN Simulation Finished Successfully.")
    except subprocess.CalledProcessError:
        print(" STOPPED: Error running ./swan.exe in WSL.")
        print(" Ensure the required libraries are installed and the file is executable.")
        sys.exit(1)