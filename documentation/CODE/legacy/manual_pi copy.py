import socket
import cv2
from picamera2 import Picamera2
from picamera2.encoders import MJPEGEncoder
from io import BytesIO
from DRV8825 import DRV8825

# 1.8 degree, fullstep cycle = 200 steps
RPI_IP = "192.168.100.2"
PC_IP = "192.168.100.1"
RPI_PORT = 5000

# Initialize Picamera2
picam2 = Picamera2()

# Start the camera preview
picam2.start()

# Initialize motors
Motor1 = DRV8825(dir_pin=13, step_pin=19, enable_pin=12)
Motor2 = DRV8825(dir_pin=24, step_pin=18, enable_pin=4)

# Initialize UDP socket
with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
    sock.connect((PC_IP, 8000))  # Replace CLIENT_IP with the receiver's IP address

    # MJPEGEncoder for efficient streaming
    encoder = MJPEGEncoder()

    # Create a BytesIO buffer for sending over the network
    stream = BytesIO()

    try:
        
        # Stream indefinitely
        while True:
            # Capture an image from the camera
            picam2.capture_file(stream, format='jpeg', encoder=encoder)

            # Send the data over the socket
            sock.sendall(stream.getvalue())

            # Clear the stream for the next frame
            stream.seek(0)
            stream.truncate()
            
    except KeyboardInterrupt:
        print("Stopping video stream...")
        picam2.stop()
