import gpiozero as GPIO
import socket
from DRV8825 import DRV8825
import time



# Motor setup (1.8 degree, fullstep cycle = 200 steps)
Motor1 = DRV8825(dir_pin=13, step_pin=19, enable_pin=12)
Motor2 = DRV8825(dir_pin=24, step_pin=18, enable_pin=4)

# Weapon and laser setup
weapon = GPIO.LED(3)
laser = GPIO.LED(21)




# Main loop to handle incoming events
def main():
    while True:
        Motor2.TurnStep(1, 1000000000, stepdelay=0.0005)

# Run the main function
if __name__ == "__main__":
    main()