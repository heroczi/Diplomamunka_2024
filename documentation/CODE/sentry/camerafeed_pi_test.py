import socket
from picamera2 import Picamera2

# Initialize camera
picam2 = Picamera2()
picam2.configure(picam2.create_still_configuration())
picam2.start()

# Establish socket connection
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(('192.168.100.1', 5000))

while True:
    # Capture image
    image = picam2.capture_array()

    # Send image to PC
    s.sendall(image.tobytes())