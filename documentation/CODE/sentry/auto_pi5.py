import socket
import pickle
import struct
import numpy as np
import cv2
import gpiozero as GPIO
from DRV8825 import DRV8825
import multiprocessing

# Constants for event types
SAFETY = 5
SHOOT_START = 2
SHOOT_STOP = 3
LASERTOGGLE = 4
STOP = 9

# Raspberry Pi IP and ports
PC_IP = "192.168.100.1"
RPI_IP = "192.168.100.2"
RPI_PORT_CONTROL = 9000
RPI_PORT_VIDEO = 2000



# Load target image and initialize ORB detector
face_cascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')

# Control command listener
def control_listener(stop_event, pos_queue):


    weapon = GPIO.LED(20)
    weapon.off()
    laser = GPIO.LED(21)
    laser.off()

    POSX, POSY = 0, 0

    safety_on = True

    sock_control = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock_control.bind((RPI_IP, RPI_PORT_CONTROL))

    print("Control process started. Safety is ON by default.")

    while not stop_event.is_set():
        data, addr = sock_control.recvfrom(1024)
        eventtype, x_movement, y_movement = map(int, data.decode().split(","))

        if eventtype == STOP:
            stop_event.set()
        elif eventtype == SAFETY:
            safety_on = not safety_on
            print("Safety ON" if safety_on else "Safety OFF")
        elif eventtype == LASERTOGGLE:
            laser.toggle()

    sock_control.close()
    print("Control process terminated.")


def Motor_motion(stop_event, pos_queue):
    Motor1 = DRV8825(dir_pin=24, step_pin=18, enable_pin=4)
    Motor2 = DRV8825(dir_pin=13, step_pin=19, enable_pin=12)

    center_x, center_y = 320, 240
    
    print("Motor process started.")
    while not stop_event.is_set():
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



# Video sending process
def video_sender(stop_event, frame_queue, pos_queue):
    camera = cv2.VideoCapture(0, cv2.CAP_V4L2)
    camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 65536)

    MAX_DGRAM = 65000
    packet_id = 0

    print("Video process started")

    while not stop_event.is_set():
        ret, frame = camera.read()
        if not ret:
            print("Error: Camera frame not captured.")
            break

        # Place the frame in the queue for processing
        if frame_queue.qsize() < 2:
            frame_queue.put(frame)

        if not pos_queue.empty():
            pos_x, pos_y = pos_queue.get()
            frame = cv2.rectangle(frame, (pos_x - 30, pos_y - 30), (pos_x + 30, pos_y + 30), (0, 0, 255), 2)



        # Encode and send the frame over UDP
        encoded, buffer = cv2.imencode('.jpg', frame)
        data = pickle.dumps(buffer)
        chunks = [data[i:i + MAX_DGRAM] for i in range(0, len(data), MAX_DGRAM)]

        for i, chunk in enumerate(chunks):
            header = struct.pack("!HHH", packet_id, i, len(chunks))
            packet = header + chunk
            server_socket.sendto(packet, (PC_IP, RPI_PORT_VIDEO))

        packet_id = (packet_id + 1) % 65535

    camera.release()
    server_socket.close()
    print("Video process terminated.")

# Target detection process
def target_detection(stop_event, frame_queue, pos_queue):
    print("Detection process started")
    while not stop_event.is_set():
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

# Main function to start processes
def main():
    stop_event = multiprocessing.Event()
    frame_queue = multiprocessing.Queue()
    pos_queue = multiprocessing.Queue()

    video_process = multiprocessing.Process(target=video_sender, args=(stop_event, frame_queue, pos_queue))
    control_process = multiprocessing.Process(target=control_listener, args=(stop_event, pos_queue))
    detection_process = multiprocessing.Process(target=target_detection, args=(stop_event, frame_queue, pos_queue))
    motor_process = multiprocessing.Process(target=Motor_motion, args=(stop_event, pos_queue))

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
