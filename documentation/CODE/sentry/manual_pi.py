import gpiozero as GPIO
import socket
import time
from DRV8825 import DRV8825
from picamera2 import Picamera2


# 1.8 degree, fullstep cycle = 200 steps
RPI_IP = "192.168.100.2"
PC_IP = "192.168.100.1"
RPI_PORT = 5000


Motor1 = DRV8825(dir_pin=13, step_pin=19, enable_pin=12)
Motor2 = DRV8825(dir_pin=24, step_pin=18, enable_pin=4)

picam2 = Picamera2()
picam2.configure(picam2.create_video_configuration(main={"size": (640, 480)}))
picam2.start()

########## Socket setup ##########
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((RPI_IP, RPI_PORT))  # Listen on the Pi's IP and port

def main():


    while True:
        # Send feed from Camera
        

        sock.sendto(bytes, PC_IP)

        # Receive mouse data
        data, addr = sock.recvfrom(1024)
        
        # Decode and split the incoming data into x and y movements
        x_movement, y_movement = map(int, data.decode().split(","))
        

        
        # Check and move motor 1 for horizontal (x) movement
        if x_movement != 0:
            #print("X Movement:", x_movement)
            dirx = 1 if x_movement > 0 else -1
            Motor1.TurnStep(dirx, 1, stepdelay=0)
            
        # Check and move motor 2 for vertical (y) movement
        if y_movement != 0:
            #print("Y Movement:", y_movement)
            diry = 1 if y_movement > 0 else -1
            Motor2.TurnStep(diry, 1, stepdelay=0)


# Start receiving mouse data
main()




    # locX = 0
    # locY = 0
    # motorLocX = 0
    # motorLocY = 0



        # locX = locX + x_movement
        # locY = locY + y_movement
        # print(locX)
        # print(locY)


        # if motorLocX != locX:
        #     dirx = 1 if locX > motorLocX else -1
        #     Motor1.TurnStep(dirx, 1, stepdelay=0)
        #     motorLocX = motorLocX + dirx
        #     print(locX-motorLocX)
        
        # if motorLocY != locY:
        #     diry = 1 if locY > motorLocY else -1
        #     Motor2.TurnStep(diry, 1, stepdelay=0)
        #     motorLocY = motorLocY + diry
        #     print(locY-motorLocY)