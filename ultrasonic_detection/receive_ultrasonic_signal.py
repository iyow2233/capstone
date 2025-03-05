import lgpio as GPIO
import time
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from collections import deque

# Set pins
TRIG = 23  # Associate pin 23 to TRIG
ECHO = 24  # Associate pin 24 to ECHO

# Open the GPIO chip and set the GPIO direction
h = GPIO.gpiochip_open(0)
GPIO.gpio_claim_output(h, TRIG)
GPIO.gpio_claim_input(h, ECHO)

# Data storage (keeping a fixed size for smoother live plotting)
timestamps = deque(maxlen=50)  # Store only the last 50 timestamps
durations = deque(maxlen=50)   # Store only the last 50 signal durations

def detect_ultrasonic_signal():
    """Detects an ultrasonic signal and logs the timestamp & duration."""
    print("Listening for ultrasonic signals...")

    # Wait for ECHO to go high (signal detected)
    while GPIO.gpio_read(h, ECHO) == 0:
        pass  # Keep waiting until a signal is received
    
    pulse_start = time.time()  # Timestamp when signal starts

    # Wait for ECHO to go low (signal ends)
    while GPIO.gpio_read(h, ECHO) == 1:
        pass  # Keep waiting until the signal stops
    
    pulse_end = time.time()  # Timestamp when signal ends
    
    pulse_duration = pulse_end - pulse_start  # Calculate duration
    timestamp = time.strftime("%H:%M:%S", time.localtime(pulse_start))  # Only time format
    
    # Store the latest data for live plotting
    timestamps.append(timestamp)
    durations.append(pulse_duration)

    print(f"[{timestamp}] Received ultrasonic signal | Duration: {pulse_duration:.6f} seconds")

# Setup real-time graph
fig, ax = plt.subplots()
ax.set_xlabel("Time (HH:MM:SS)")
ax.set_ylabel("Signal Duration (seconds)")
ax.set_title("Live Ultrasonic Signal Detection")
line, = ax.plot([], [], marker='o', linestyle='-', color='b')

def update_plot(frame):
    """Updates the live plot with new data."""
    if not timestamps:
        timestamps.append("00:00:00")  # Placeholder timestamp
        durations.append(0)  # Default zero duration to show a line
    
    ax.clear()
    ax.set_xlabel("Time (HH:MM:SS)")
    ax.set_ylabel("Signal Duration (seconds)")
    ax.set_title("Live Ultrasonic Signal Detection")
    ax.plot(timestamps, durations, marker='o', linestyle='-', color='b')
    ax.set_xticklabels(timestamps, rotation=45)
    ax.grid()

    return line,

# Initialize live updating graph
ani = animation.FuncAnimation(fig, update_plot, interval=1000)

# Main program
if __name__ == '__main__':
    try:
        while True:
            detect_ultrasonic_signal()
            time.sleep(1)  # Wait 1 second before checking again

            # Display graph every 10 data points
            if len(timestamps) % 10 == 0:
                plot_graph()

    except KeyboardInterrupt:
        print("Listening stopped by User")
        GPIO.gpiochip_close(h)
        plt.show()  # Show final graph before exiting
