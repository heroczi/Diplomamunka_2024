import socket
import pickle
import struct
import numpy as np
import cv2
import gpiozero as GPIO
from DRV8825 import DRV8825
import multiprocessing

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
PC_IP = "192.168.100.1"
RPI_IP = "192.168.100.2"
RPI_PORT_CONTROL = 9000
RPI_PORT_VIDEO = 2000

# Motor setup
Motor1 = DRV8825(dir_pin=24, step_pin=18, enable_pin=4)
Motor2 = DRV8825(dir_pin=13, step_pin=19, enable_pin=12)

def setup_gpio_pins():
    """Set up GPIO pins for weapon and laser."""
    weapon, laser = GPIO.LED(20), GPIO.LED(21)
    weapon.off()
    laser.off()
    return weapon, laser

def video_sender(stop_event, automode_event, frame_queue, pos_queue):
    """Send video frames via UDP to the PC."""
    MAX_DGRAM = 65000
    packet_id = 0

    camera = cv2.VideoCapture(0, cv2.CAP_V4L2)
    camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as server_socket:
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 65536)
        print("Video process started")

        try:
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

                encoded, buffer = cv2.imencode('.jpg', frame)
                data = pickle.dumps(buffer)
                chunks = [data[i:i + MAX_DGRAM] for i in range(0, len(data), MAX_DGRAM)]

                for i, chunk in enumerate(chunks):
                    header = struct.pack("!HHH", packet_id, i, len(chunks))
                    server_socket.sendto(header + chunk, (PC_IP, RPI_PORT_VIDEO))

                packet_id = (packet_id + 1) % 65535
        finally:
            camera.release()
            print("Video process terminated.")

def target_detection(stop_event, automode_event, frame_queue, pos_queue):
    """Detect target faces in the frame."""
    face_cascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')
    print("Detection process started")

    try:
        while not stop_event.is_set():
            if automode_event.is_set() and not frame_queue.empty():
                frame = frame_queue.get()
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces = face_cascade.detectMultiScale(gray, 1.3, 5)
                
                if len(faces) > 0:
                    x, y, w, h = max(faces, key=lambda rect: rect[2] * rect[3])
                    pos_queue.put((x + w // 2, y + h // 2))
    finally:
        print("Detection process terminated.")

def control_listener(stop_event, automode_event):
    """Process control commands from the PC."""
    weapon, laser = setup_gpio_pins()
    safety_on = True

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock_control:
        sock_control.bind((RPI_IP, RPI_PORT_CONTROL))
        print("Control process started.")

        try:
            while not stop_event.is_set():
                data, _ = sock_control.recvfrom(1024)
                eventtype, x_movement, y_movement = map(int, data.decode().split(","))

                if eventtype == STOP:
                    stop_event.set()
                elif eventtype == MANUALMODE:
                    automode_event.clear()
                elif eventtype == AUTOMODE:
                    automode_event.set()
                elif eventtype == SAFETY:
                    safety_on = not safety_on
                    print("Safety", "ON" if safety_on else "OFF")
                elif eventtype == MOVE and not automode_event.is_set():
                    if x_movement != 0:
                        dirx = 1 if x_movement > 0 else -1
                        Motor1.TurnStep(dirx, 1, 0)
                    if y_movement != 0:
                        diry = 1 if y_movement > 0 else -1
                        Motor2.TurnStep(diry, 1, 0)
                elif eventtype == SHOOT_START and not safety_on:
                    weapon.on()
                elif eventtype == SHOOT_STOP:
                    weapon.off()
                elif eventtype == LASERTOGGLE:
                    laser.toggle()
        finally:
            print("Control process terminated.")
            weapon.off()
            laser.off()
    

def motor_motion(stop_event, automode_event, pos_queue):
    """Move motors to align with the target position."""
    center_x, center_y = 320, 240
    print("Motor process started.")

    try:
        while not stop_event.is_set():
            if automode_event.is_set() and not pos_queue.empty():
                target_x, target_y = pos_queue.get()
                error_x, error_y = target_x - center_x, target_y - center_y

                if abs(error_x) > 10:
                    Motor1.TurnStep(1 if error_x > 0 else -1, abs(error_x) - 1, 0.0005)
                if abs(error_y) > 10:
                    Motor2.TurnStep(1 if error_y > 0 else -1, abs(error_y) - 1, 0.0005)
    finally:
        print("Motors process terminated.")

def main():
    """Initialize and start all processes."""
    stop_event, automode_event = multiprocessing.Event(), multiprocessing.Event()
    frame_queue, pos_queue = multiprocessing.Queue(), multiprocessing.Queue()

    processes = [
        multiprocessing.Process(target=video_sender, args=(stop_event, automode_event, frame_queue, pos_queue)),
        multiprocessing.Process(target=control_listener, args=(stop_event, automode_event)),
        multiprocessing.Process(target=target_detection, args=(stop_event, automode_event, frame_queue, pos_queue)),
        multiprocessing.Process(target=motor_motion, args=(stop_event, automode_event, pos_queue))
    ]

    # Start all processes
    for process in processes:
        process.start()

    # Wait for all processes to complete
    for process in processes:
        process.join()

    # Clean up queues
    frame_queue.close()
    frame_queue.join_thread()
    pos_queue.close()
    pos_queue.join_thread()

    automode_event.clear()

    print("All processes and queues terminated.")

if __name__ == "__main__":
    main()
