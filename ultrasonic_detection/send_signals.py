import lgpio as GPIO
import time

# Set pin
TRIG = 17  # Associate pin 17 to TRIG (signal sender)
ECHO = 27

# Open the GPIO chip and set the GPIO direction
h = GPIO.gpiochip_open(0)
GPIO.gpio_claim_output(h, TRIG)  # Set TRIG as an output
GPIO.gpio_claim_input(h, ECHO)

def send_ultrasonic_signal():
    """Sends an ultrasonic pulse on TRIG."""
    print("Sending ultrasonic pulse...")
    GPIO.gpio_write(h, TRIG, 0)
    time.sleep(2)  # Ensure sensor stability
    
    # Send a brief pulse to trigger
    GPIO.gpio_write(h, TRIG, 1)
    time.sleep(0.00001)  # Send a 10-microsecond pulse
    GPIO.gpio_write(h, TRIG, 0)
    print("Pulse sent.")

    # Start recording the time when the wave is sent
    while GPIO.gpio_read(h, ECHO) == 0:
        pulse_start = time.time()

    # Record time of arrival
    while GPIO.gpio_read(h, ECHO) == 1:
        pulse_end = time.time()

    # Calculate the difference in times
    pulse_duration = pulse_end - pulse_start

    print(pulse_duration)

# Main program
if __name__ == '__main__':
    try:
        while True:
            send_ultrasonic_signal()
            time.sleep(1)  # Wait 1 second before sending again

    except KeyboardInterrupt:
        print("Ultrasonic signal sending stopped by User")
        GPIO.gpiochip_close(h)
