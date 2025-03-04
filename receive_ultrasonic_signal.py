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
    print("Listening for ultrasonic signals...")

    # Wait for ECHO to go high (signal detected)
    while GPIO.gpio_read(h, ECHO) == 0:
        pass  # Keep waiting until a signal is received

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
