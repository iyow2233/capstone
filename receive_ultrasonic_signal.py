import lgpio as GPIO
import time

# Set pins
TRIG = 23  # Associate pin 23 to TRIG
ECHO = 24  # Associate pin 24 to ECHO

# Open the GPIO chip and set the GPIO direction
h = GPIO.gpiochip_open(0)
GPIO.gpio_claim_output(h, TRIG)
GPIO.gpio_claim_input(h, ECHO)

def detect_ultrasonic_signal():
    GPIO.gpio_write(h, TRIG, 0)
    time.sleep(2)

    # Send a brief pulse to trigger
    GPIO.gpio_write(h, TRIG, 1)
    time.sleep(0.00001)
    GPIO.gpio_write(h, TRIG, 0)

    # Wait for ECHO to go high
    while GPIO.gpio_read(h, ECHO) == 0:
        pass  # Wait until the signal starts

    print("Received ultrasonic signal")

# Main program
if __name__ == '__main__':
    try:
        while True:
            detect_ultrasonic_signal()
            time.sleep(1)

    except KeyboardInterrupt:
        print("Measurement stopped by User")
        GPIO.gpiochip_close(h)
