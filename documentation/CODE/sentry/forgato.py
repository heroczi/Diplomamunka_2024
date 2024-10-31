import gpiozero as GPIO
from DRV8825 import DRV8825




# Motor setup (1.8 degree, fullstep cycle = 200 steps)
Motor1 = DRV8825(dir_pin=13, step_pin=19, enable_pin=12)
Motor2 = DRV8825(dir_pin=24, step_pin=18, enable_pin=4)



# Main loop to handle incoming events
def main():
    while True:
        Motor1.TurnStep(1, 2000, stepdelay=0.0005)
        Motor1.TurnStep(-1, 2000, stepdelay=0.0005)
        Motor1.TurnStep(1, 2000, stepdelay=0.001)
        Motor1.TurnStep(-1, 2000, stepdelay=0.001)
        Motor1.TurnStep(1, 2000, stepdelay=0.002)
        Motor1.TurnStep(-1, 2000, stepdelay=0.002)
        Motor1.TurnStep(1, 2000, stepdelay=0.003)
        Motor1.TurnStep(-1, 2000, stepdelay=0.003)
# Run the main function
if __name__ == "__main__":
    main()