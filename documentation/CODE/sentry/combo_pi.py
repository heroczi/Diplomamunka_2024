import socket
import pickle
import struct
import numpy as np
import cv2
import gpiozero as GPIO
from DRV8825 import DRV8825
import multiprocessing
import struct

# Constants for event types
MOVE = 1
SHOOT_START = 2
SHOOT_STOP = 3
LASERTOGGLE = 4
SAFETY = 5
MANUALMODE = 6
AUTOMODE = 7
STOP = 9

# Raspberry Pi IP and ports
PC_IP = "192.168.100.1"  # PC's IP address
RPI_IP = "192.168.100.2"
RPI_PORT_CONTROL = 9000  # Port for receiving control commands
RPI_PORT_VIDEO = 2000     # Port for sending video frames

Motor1 = DRV8825(dir_pin=24, step_pin=18, enable_pin=4)
Motor2 = DRV8825(dir_pin=13, step_pin=19, enable_pin=12)
# Control command listener
def control_listener(stop_event, automode_event):
   
    weapon = GPIO.LED(20)
    weapon.off()
    laser = GPIO.LED(21)
    laser.off()

    safety_on = True
     
    sock_control = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock_control.bind((RPI_IP, RPI_PORT_CONTROL))

    print("Control process started. ")

    while not stop_event.is_set():
        try:
            data, addr = sock_control.recvfrom(1024)
            eventtype, x_movement, y_movement = map(int, data.decode().split(","))
            
            if eventtype == STOP:
                stop_event.set()

            elif eventtype == MANUALMODE:
                automode_event.clear()

            elif eventtype == AUTOMODE:
                automode_event.set()

            elif eventtype == SAFETY:
                safety_on = not safety_on
                print("Safety ON" if safety_on else "Safety OFF")

            elif eventtype == MOVE:
                if not automode_event.is_set():
                    if x_movement != 0:
                        dirx = 1 if x_movement > 0 else -1
                        Motor1.TurnStep(dirx, 1, 0)

                    if y_movement != 0:
                        diry = 1 if y_movement > 0 else -1
                        Motor2.TurnStep(diry, 1, 0)

            elif eventtype == SHOOT_START:
                if not safety_on:
                    weapon.on()
            elif eventtype == SHOOT_STOP:
                weapon.off()
            elif eventtype == LASERTOGGLE:
                laser.toggle()

        except Exception as e:
            print(f"Control error: {e}")

    sock_control.close()
    print("Control process terminated.")

def video_sender(stop_event, automode_event, frame_queue, pos_queue):
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
        

        if automode_event.is_set():
            if frame_queue.qsize() < 2:
                frame_queue.put(frame)

            if not pos_queue.empty():
                pos_x, pos_y = pos_queue.get()
                frame = cv2.rectangle(frame, (pos_x - 30, pos_y - 30), (pos_x + 30, pos_y + 30), (0, 0, 255), 2)

        
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


def target_detection(stop_event, automode_event, frame_queue, pos_queue):
    face_cascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')
    print("Detection process started")

    while not stop_event.is_set():
        if automode_event.is_set():
            if not frame_queue.empty():
                frame = frame_queue.get()
                
                # Convert frame to grayscale for face detection
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                
                # Detect faces
                faces = face_cascade.detectMultiScale(gray, 1.3, 5)
                
                # Find the largest face (best match)
                if len(faces) > 0:
                    largest_face = max(faces, key=lambda rect: rect[2] * rect[3])
                    x, y, w, h = largest_face
                    center_x, center_y = x + w // 2, y + h // 2
                    pos_queue.put((center_x, center_y))
                    print(f"Face found at: ({center_x}, {center_y})")
    print("Detection process terminated.")

def Motor_motion(stop_event,automode_event, pos_queue):
    

    center_x, center_y = 320, 240
    
    print("Motor process started.")
    while not stop_event.is_set():
        if automode_event.is_set():
        # Update the target position from the queue if available
            if not pos_queue.empty():
                target_x, target_y = pos_queue.get()
                print(f"New target received: ({target_x}, {target_y})")
            else:
                target_x, target_y = 320, 240


            error_x = target_x - center_x
            error_y = target_y - center_y

            if abs(error_x) > 10:  # Minimum threshold to avoid micro-steps
                direction_x = 1 if error_x > 0 else -1
                print("X steps: ", abs(error_x)-1)
                Motor1.TurnStep(direction_x, max(1, abs(error_x)-1), 0.0005)

            if abs(error_y) > 10:
                direction_y = 1 if error_y > 0 else -1
                print("X steps: ", abs(error_y)-1)
                Motor2.TurnStep(direction_y, max(1, abs(error_x)-1), 0.0005)

    print("Motors process terminated.")


# Main function to start both threads
def main():
    stop_event = multiprocessing.Event()
    automode_event = multiprocessing.Event()

    frame_queue = multiprocessing.Queue()
    pos_queue = multiprocessing.Queue()

    video_process = multiprocessing.Process(target=video_sender, args=(stop_event, automode_event, frame_queue, pos_queue))
    control_process = multiprocessing.Process(target=control_listener, args=(stop_event, automode_event))
    detection_process = multiprocessing.Process(target=target_detection, args=(stop_event, automode_event, frame_queue, pos_queue))
    motor_process = multiprocessing.Process(target=Motor_motion, args=(stop_event, automode_event, pos_queue))

    # Start the processes
    video_process.start()
    motor_process.start()
    control_process.start()
    detection_process.start()

    # Wait for all processes to complete
    video_process.join()
    motor_process.join()
    control_process.join()
    detection_process.join()

    print("All processes terminated.")

if __name__ == "__main__":

    main()
