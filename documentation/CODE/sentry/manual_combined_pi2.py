import socket
import struct
import numpy as np
import cv2
import gpiozero as GPIO
from DRV8825 import DRV8825
import multiprocessing
from picamera2 import Picamera2


# Constants for event types
MOVE = 1
SHOOT_START = 2
SHOOT_STOP = 3
LASERTOGGLE = 4

# Raspberry Pi IP and ports
PC_IP = "192.168.100.1"  # PC's IP address
RPI_IP = "192.168.100.2"
RPI_PORT_CONTROL = 9000  # Port for receiving control commands
RPI_PORT_VIDEO = 2000     # Port for sending video frames

# Motor setup
Motor1 = DRV8825(dir_pin=13, step_pin=19, enable_pin=12)
Motor2 = DRV8825(dir_pin=24, step_pin=18, enable_pin=4)

# Weapon and laser setup
weapon = GPIO.LED(3)
laser = GPIO.LED(21)



# Motor control functions
def move_motor(motor, direction, steps=1, delay=0):
    motor.TurnStep(direction, steps, stepdelay=delay)

def handle_move(x_movement, y_movement):
    if x_movement != 0:
        dirx = 1 if x_movement > 0 else -1
        move_motor(Motor1, dirx)

    if y_movement != 0:
        diry = 1 if y_movement > 0 else -1
        move_motor(Motor2, diry)

# Event handler functions
def handle_shoot_start():
    weapon.on()

def handle_shoot_stop():
    weapon.off()

def handle_laser_toggle():
    laser.toggle()
    print("Laser toggled")

# Control command listener
def control_listener():

    # Socket for control commands
    sock_control = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock_control.bind((RPI_IP, RPI_PORT_CONTROL))

    while True:
        try:
            data, addr = sock_control.recvfrom(1024)
            eventtype, x_movement, y_movement = map(int, data.decode().split(","))
            
            if eventtype == MOVE:
                handle_move(x_movement, y_movement)
            elif eventtype == SHOOT_START:
                handle_shoot_start()
            elif eventtype == SHOOT_STOP:
                handle_shoot_stop()
            elif eventtype == LASERTOGGLE:
                handle_laser_toggle()
        except Exception as e:
            print(f"Control error: {e}")

# Video frame sender
def video_sender():

    # Initialize the PiCamera2
    picam2 = Picamera2()
    picam2.configure(picam2.create_video_configuration(main={"size": (640, 480)}))
    picam2.start()

    # Socket for sending video feed
    sock_video = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    CHUNK_SIZE =  65535 # Maximum size for UDP packets

    while True:

        # Capture a frame from the camera
        frame = picam2.capture_array()

        # Encode the frame using JPEG to compress and reduce size
        ret, encoded_frame = cv2.imencode('.jpg', frame)
        if not ret:
            continue  # Skip if encoding fails

        # Prepare data: send frame size followed by the frame data
        frame_data = encoded_frame.tobytes()
        frame_size = len(frame_data)
        if frame_size < CHUNK_SIZE:
            # Send frame size as a 4-byte unsigned integer (big-endian)
            sock_video.sendto(struct.pack(">I", frame_size), (PC_IP, RPI_PORT_VIDEO))

            # Send the actual frame data in chunks
            
            for i in range(0, frame_size, CHUNK_SIZE):
                sock_video.sendto(frame_data[i:i + CHUNK_SIZE], (PC_IP, RPI_PORT_VIDEO))




# Main function to start both threads
def main():
    video_process = multiprocessing.Process(target=video_sender)
    control_process = multiprocessing.Process(target=control_listener)

    # Start the processes
    video_process.start()
    control_process.start()

    # Wait for both processes to finish
    video_process.join()
    control_process.join()

if __name__ == "__main__":

    main()
