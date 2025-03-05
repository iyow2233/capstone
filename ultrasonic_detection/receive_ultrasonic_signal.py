import lgpio as GPIO
import time
import matplotlib.pyplot as plt

# Set pins
TRIG = 23  # Associate pin 23 to TRIG
ECHO = 24  # Associate pin 24 to ECHO

# Open the GPIO chip and set the GPIO direction
h = GPIO.gpiochip_open(0)
GPIO.gpio_claim_output(h, TRIG)
GPIO.gpio_claim_input(h, ECHO)
# Lists to store data for plotting
timestamps = []
durations = []

def detect_ultrasonic_signal():
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
    
    # Store data
    timestamps.append(timestamp)
    durations.append(pulse_duration)

    print(f"[{timestamp}] Received ultrasonic signal | Duration: {pulse_duration:.6f} seconds")

def plot_graph():
    """ Function to plot the signal durations over time """
    plt.figure(figsize=(10, 5))
    plt.plot(timestamps, durations, marker='o', linestyle='-', color='b', label="Signal Duration")
    plt.xlabel("Time (HH:MM:SS)")
    plt.ylabel("Signal Duration (seconds)")
    plt.title("Ultrasonic Signal Detection Over Time")
    plt.xticks(rotation=45)
    plt.legend()
    plt.grid()
    plt.show()

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
        plot_graph()  # Show final graph before exiting
