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

POSX, POSY = 0, 0


def setup_gpio_pins():
    """Set up GPIO pins for weapon and laser."""
    weapon, laser = GPIO.LED(20), GPIO.LED(21)
    weapon.off()
    laser.off()

    #angle2_VCC = PIN17
    angle1_GND = GPIO.LED(22)
    angle1_GND.off()
    angle1_SIG = GPIO.Button(27, pull_up = False)

    angle2_VCC = GPIO.LED(11)
    angle2_VCC.on()
    #angle2_GND = PIN25
    angle2_SIG = GPIO.Button(0, pull_up = False)
    return weapon, laser, angle1_SIG, angle2_SIG

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
    weapon, laser, angle1, angle2 = setup_gpio_pins()
    safety_on = True

    while not angle1.is_pressed:
        Motor1.TurnStep(1, 1, 0.0005)
    
    Motor1.TurnStep(-1, 78, 0.0005) # 35°

    POSX = 0

    while not angle2.is_pressed:
        Motor2.TurnStep(1, 1, 0.0005)

    Motor2.TurnStep(-1, 55, 0.0005) # 25°

    POSY = 0

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


                    if x_movement > 0 and POSX < 300: # 150
                        dirx = 1
                        Motor1.TurnStep(dirx, 1, 0)
                        POSX = POSX + dirx
                    
                    if x_movement < 0 and POSX > -300: # -150
                        dirx = -1
                        Motor1.TurnStep(dirx, 1, 0)
                        POSX = POSX + dirx

                    if y_movement > 0 and POSY < 155: # 70
                        diry = 1
                        Motor2.TurnStep(diry, 1, 0)
                        POSY = POSY + diry
                    
                    if y_movement < 0 and POSY > -45: # -20
                        diry = -1
                        Motor2.TurnStep(diry, 1, 0)
                        POSY = POSY + diry

                elif eventtype == SHOOT_START and not safety_on:
                    weapon.on()
                elif eventtype == SHOOT_STOP:
                    weapon.off()
                elif eventtype == LASERTOGGLE:
                    laser.toggle()
        finally:
            Motor1.TurnStep(POSX/abs(POSX), abs(POSX), 0.0005) # X centering before shutdown
            Motor2.TurnStep(POSY/abs(POSY), abs(POSY), 0.0005) # Y centering before shutdown
            print("Control process terminated.")
            weapon.off()
            laser.off()
    

def motor_motion(stop_event, automode_event, pos_queue):
    """Move motors to align with the target position."""
    center_x, center_y = 326, 216
    print("Motor process started.")

    try:
        while not stop_event.is_set():
            if automode_event.is_set() and not pos_queue.empty():
                target_x, target_y = pos_queue.get()
                error_x, error_y = target_x - center_x, target_y - center_y

                if abs(error_x) > 10 and abs(POSX) < 300:
                    Motor1.TurnStep(1 if error_x > 0 else -1, abs(error_x) - 1, 0.0005)
                if abs(error_y) > 10 and -50 < POSY < 150:
                    Motor2.TurnStep(1 if error_y > 0 else -1, abs(error_y) - 1, 0.0005)

                if error_x > 10 and POSX < 300: # X axis limit to the left 150°
                    dirx = 1
                    Motor1.TurnStep(1, abs(error_x) - 1, 0.0005)
                    POSX = POSX + dirx
                    
                if error_x < -10 and POSX > -300: # X axis limit to the right -150°
                    dirx = -1
                    Motor1.TurnStep(-1, abs(error_x) - 1, 0.0005)
                    POSX = POSX + dirx

                if error_y > 10 and POSY < 155: # Y axis limit to the top 70°
                    diry = 1
                    Motor2.TurnStep(1, abs(error_y) - 1, 0.0005)
                    POSY = POSY + diry
                    
                if error_y < 10 and POSY > -45: # Y axis limit to the bottom -20
                    diry = -1
                    Motor2.TurnStep(-1, abs(error_y) - 1, 0.0005)
                    POSY = POSY + diry


    
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

    print("All processes and queues terminated.")

if __name__ == "__main__":
    main()
