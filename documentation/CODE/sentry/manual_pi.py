import gpiozero as GPIO
import socket
from DRV8825 import DRV8825

# 1.8 degree, fullstep cycle = 200 steps
RPI_IP = "192.168.100.2"
PC_IP = "192.168.100.1"
RPI_PORT = 5000


Motor1 = DRV8825(dir_pin=13, step_pin=19, enable_pin=12)
Motor2 = DRV8825(dir_pin=24, step_pin=18, enable_pin=4)

########## Socket setup ##########
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((RPI_IP, RPI_PORT))  # Listen on the Pi's IP and port

def main():

    while True:

        # Receive mouse data
        data, addr = sock.recvfrom(1024)
        
        # Decode and split the incoming data into x and y movements
        x_movement, y_movement = map(int, data.decode().split(","))
        

        # Check and move motor 1 for horizontal (x) movement
        if x_movement != 0:
            dirx = 1 if x_movement > 0 else -1
            print("X Movement:", x_movement)
            print("X direction:", dirx)
            Motor1.TurnStep(dirx, 1, stepdelay=0)
            
        # Check and move motor 2 for vertical (y) movement
        if y_movement != 0:
            diry = 1 if y_movement > 0 else -1
            print("Y Movement:", y_movement)
            print("Y direction:", diry)
            Motor2.TurnStep(diry, 1, stepdelay=0)


# Start receiving mouse data
main()
