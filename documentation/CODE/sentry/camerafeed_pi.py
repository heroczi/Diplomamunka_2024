import socket
import cv2
import struct
import pickle
from picamera2 import Picamera2

# Set up the camera
picam2 = Picamera2()
picam2.configure(picam2.create_video_configuration(main={"size": (640, 480)}))
picam2.start()

# Create a TCP/IP socket
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Bind the socket to the server IP and port
server_ip = '192.168.100.2'  # Change this to your Raspberry Pi's static IP address
port = 8000
server_socket.bind((server_ip, port))

# Start listening for connections
server_socket.listen(1)
print("Waiting for connection...")

# Accept a connection
connection, client_address = server_socket.accept()
print(f"Connection from {client_address}")

# Send video feed
try:
    while True:
        # Capture a frame from the camera
        frame = picam2.capture_array()

        # Encode the frame as JPEG
        encoded, buffer = cv2.imencode('.jpg', frame)

        # Serialize the frame
        data = pickle.dumps(buffer)

        # Send the size of the frame, followed by the frame data itself
        message_size = struct.pack("L", len(data))  # L: unsigned long
        connection.sendall(message_size + data)

finally:
    connection.close()
    server_socket.close()