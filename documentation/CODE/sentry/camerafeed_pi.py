import socket
import cv2
import struct
from picamera2 import Picamera2

# Initialize the UDP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_ip = '192.168.100.1'  # Replace with your PC's IP address
server_port = 8000
server_address = (server_ip, server_port)

# Initialize the PiCamera2
picam2 = Picamera2()
picam2.configure(picam2.create_video_configuration(main={"size": (640, 480)}))
picam2.start()

while True:
    # Capture a frame
    frame = picam2.capture_array()

    # Encode the frame using JPEG to compress and reduce size
    ret, encoded_frame = cv2.imencode('.jpg', frame)
    if not ret:
        continue  # Skip if encoding fails

    # Prepare data: send frame size followed by the frame data
    frame_data = encoded_frame.tobytes()
    frame_size = len(frame_data)

    # Send frame size as a 4-byte unsigned integer (big-endian)
    sock.sendto(struct.pack(">I", frame_size), server_address)

    # Send the actual frame data in chunks (UDP has a limit, so split if necessary)
    CHUNK_SIZE = 65507  # Maximum size for UDP packets
    for i in range(0, frame_size, CHUNK_SIZE):
        sock.sendto(frame_data[i:i + CHUNK_SIZE], server_address)

sock.close()