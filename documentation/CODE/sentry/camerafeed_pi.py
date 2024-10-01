import socket
import cv2
import numpy as np
from picamera2 import Picamera2

# Configure the camera
picam2 = Picamera2()
picam2.configure(picam2.create_video_configuration(main={"size": (1920, 1080)}))
picam2.start()

# Socket setup
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind(('192.168.100.2', 6000))  # Bind to the Pi's IP and port 5000
server_socket.listen(1)
print("Waiting for a connection...")
conn, addr = server_socket.accept()
print("Connected to:", addr)

try:
    while True:
        # Capture frame
        frame = picam2.capture_array()

        # Compress the frame using JPEG to reduce the data size
        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 90]
        result, frame = cv2.imencode('.jpg', frame, encode_param)

        # Convert frame to bytes
        data = frame.tobytes()

        # Send the size of the frame first
        conn.sendall(len(data).to_bytes(4, byteorder='big'))

        # Send the frame
        conn.sendall(data)

except Exception as e:
    print(f"Error: {e}")

finally:
    conn.close()
    server_socket.close()
