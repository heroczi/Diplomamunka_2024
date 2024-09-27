import socket
import cv2
from picamera2 import Picamera2
from picamera2.encoders import MJPEGEncoder
from io import BytesIO

RPI_IP = "192.168.100.2"
PC_IP = "192.168.100.1"
RPI_PORT = 5000

# Initialize Picamera2
picam2 = Picamera2()

# Start the camera preview
picam2.start()

# Initialize UDP socket
with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
    sock.connect((PC_IP, RPI_PORT))  # Replace CLIENT_IP with the receiver's IP address

    # Create a BytesIO buffer for sending over the network
    stream = BytesIO()

    try:
        print("Streaming video indefinitely. Press Ctrl+C to stop.")
        
        # Stream indefinitely
        while True:
            # Capture an image from the camera
            picam2.capture_file(stream, format='jpeg')

            # Send the data over the socket
            sock.sendall(stream.getvalue())

            # Clear the stream for the next frame
            stream.seek(0)
            stream.truncate()
            
    except KeyboardInterrupt:
        print("Stopping video stream...")
        picam2.stop()