import gpiozero as GPIO
import socket
from DRV8825 import DRV8825
import time

# Constants for event types
MOVE = 1
SHOOT_START = 2
SHOOT_STOP = 3
LASERTOGGLE = 4

# Raspberry Pi IP and Port for socket communication
RPI_IP = "192.168.100.2"
RPI_PORT = 5000

# Motor setup (1.8 degree, fullstep cycle = 200 steps)
Motor1 = DRV8825(dir_pin=13, step_pin=19, enable_pin=12)
Motor2 = DRV8825(dir_pin=24, step_pin=18, enable_pin=4)

# Weapon and laser setup
weapon = GPIO.LED(3)
laser = GPIO.LED(21)

# Socket setup
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((RPI_IP, RPI_PORT))  # Listen on the Pi's IP and port

# Motor control functions
def move_motor(motor, direction, steps=1, delay=0):
    """Move a motor by a specified number of steps in the given direction."""
    motor.TurnStep(direction, steps, stepdelay=delay)

def handle_move(x_movement, y_movement):
    """Handle MOVE events for both horizontal and vertical movement."""
    # Move Motor1 (horizontal)
    if x_movement != 0:
        dirx = 1 if x_movement > 0 else -1
        move_motor(Motor1, dirx)

    # Move Motor2 (vertical)
    if y_movement != 0:
        diry = 1 if y_movement > 0 else -1
        move_motor(Motor2, diry)

# Event handler functions
def handle_shoot_start():
    """Handle SHOOT_START event."""
    weapon.on()

def handle_shoot_stop():
    """Handle SHOOT_STOP event."""
    weapon.off()

def handle_laser_toggle():
    """Handle LASERTOGGLE event."""
    laser.toggle()
    print("Laser toggled")

# Main loop to handle incoming events
def main():
    print(f"Listening for UDP packets on {RPI_IP}:{RPI_PORT}...")

    while True:
        try:
            # Receive mouse data
            data, addr = sock.recvfrom(1024)
            eventtype, x_movement, y_movement = map(int, data.decode().split(","))
            
            # Process events based on the event type
            if eventtype == MOVE:
                handle_move(x_movement, y_movement)

            elif eventtype == SHOOT_START:
                handle_shoot_start()

            elif eventtype == SHOOT_STOP:
                handle_shoot_stop()

            elif eventtype == LASERTOGGLE:
                handle_laser_toggle()

        except KeyboardInterrupt:
            print("\nTerminating the program.")
            break

        except Exception as e:
            print(f"Error: {e}")

# Run the main function
if __name__ == "__main__":
    main()