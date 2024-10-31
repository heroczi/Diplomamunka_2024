import socket
import pickle
import struct
import numpy as np
import cv2
import gpiozero as GPIO
from DRV8825 import DRV8825
import multiprocessing
from picamera2 import Picamera2
import struct

# Constants for event types
MOVE = 1
SHOOT_START = 2
SHOOT_STOP = 3
LASERTOGGLE = 4
STOP = 9

# Raspberry Pi IP and ports
PC_IP = "192.168.100.1"  # PC's IP address
RPI_IP = "192.168.100.2"
RPI_PORT_CONTROL = 9000  # Port for receiving control commands
RPI_PORT_VIDEO = 2000     # Port for sending video frames

# Control command listener
def control_listener(stop_event):

    Motor1 = DRV8825(dir_pin=13, step_pin=19, enable_pin=12)
    Motor2 = DRV8825(dir_pin=24, step_pin=18, enable_pin=4)

    weapon = GPIO.LED(20)
    weapon.off()
    laser = GPIO.LED(21)
    laser.off()

    #vegallas1_VCC = PIN17
    vegallas1_GND = GPIO.LED(22)
    vegallas1_GND.off()
    vegallas1_SIG = GPIO.Button(27, pull_up = False)

    vegallas2_VCC = GPIO.LED(11)
    vegallas2_VCC.on()
    #vegallas2_GND = PIN25
    vegallas2_SIG = GPIO.Button(0, pull_up = False)

    sock_control = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock_control.bind((RPI_IP, RPI_PORT_CONTROL))

    print("Control process started. ")

    # while not vegallas1_SIG.is_pressed:
    #     Motor1.TurnStep(1, 1, 0.0005)
    # while not vegallas2_SIG.is_pressed:
    #     Motor2.TurnStep(1, 1, 0.0005)

    POSX = 0
    POSY = 0

    while not stop_event.is_set():
        try:
            data, addr = sock_control.recvfrom(1024)
            eventtype, x_movement, y_movement = map(int, data.decode().split(","))
            
            if eventtype == STOP:
                stop_event.set()

            elif eventtype == MOVE:
                if x_movement != 0:
                    dirx = 1 if x_movement > 0 else -1
                    Motor1.TurnStep(dirx, 1, 0)
                    POSX = POSX + 18*dirx

                if y_movement != 0:
                    diry = 1 if y_movement > 0 else -1
                    Motor2.TurnStep(diry, 1, 0)
                    POSY = POSY + 18*diry

                print(POSX/100,POSY/100)

            elif eventtype == SHOOT_START:
                weapon.on()
            elif eventtype == SHOOT_STOP:
                weapon.off()
            elif eventtype == LASERTOGGLE:
                laser.toggle()
        except Exception as e:
            print(f"Control error: {e}")

    sock_control.close()
    print("Control process terminated.")

def video_sender(stop_event):
    camera = cv2.VideoCapture(0, cv2.CAP_V4L2)
    camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    # Set up UDP socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 65536)

    MAX_DGRAM = 65000  # Max datagram size, less than 65507 to allow for headers
    packet_id = 0

    print("Video process started")
    while not stop_event.is_set():
        ret, frame = camera.read()
        if not ret:
            break

        # Encode the frame as JPEG
        encoded, buffer = cv2.imencode('.jpg', frame)
        data = pickle.dumps(buffer)
        
        # Split data into chunks
        chunks = [data[i:i + MAX_DGRAM] for i in range(0, len(data), MAX_DGRAM)]

        for i, chunk in enumerate(chunks):
            # Create a header with packet_id, chunk index, and total number of chunks
            header = struct.pack("!HHH", packet_id, i, len(chunks))
            packet = header + chunk
            server_socket.sendto(packet, (PC_IP, RPI_PORT_VIDEO))

        # Increment packet ID to help the receiver with reassembly
        packet_id = (packet_id + 1) % 65535

    camera.release()
    server_socket.close()
    print("Video process terminated.")


# Main function to start both threads
def main():
    stop_event = multiprocessing.Event()
    video_process = multiprocessing.Process(target=video_sender, args=(stop_event,))
    control_process = multiprocessing.Process(target=control_listener, args=(stop_event,))

    # Start the processes
    video_process.start()
    control_process.start()

    # Wait for both processes to finish
    video_process.join()
    control_process.join()
    print("All processes terminated.")

if __name__ == "__main__":

    main()
