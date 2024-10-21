import cv2
import socket
import pickle
import struct
import numpy as np

# Set up socket to receive video stream from Raspberry Pi
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect(('192.168.100.1', 7000))  # Change to your Raspberry Pi IP and port

data = b""
payload_size = struct.calcsize("L")

while True:
    # Receive the size of the incoming frame
    while len(data) < payload_size:
        packet = client_socket.recv(4096)  # Adjust buffer size if needed
        if not packet:
            break
        data += packet

    packed_msg_size = data[:payload_size]
    data = data[payload_size:]
    msg_size = struct.unpack("L", packed_msg_size)[0]

    # Receive the frame
    while len(data) < msg_size:
        data += client_socket.recv(4096)

    frame_data = data[:msg_size]
    data = data[msg_size:]

    # Deserialize the frame
    frame = pickle.loads(frame_data)

    # Display the frame
    cv2.imshow('Video Feed', frame)
    
    # Exit the window with 'q'
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

client_socket.close()
cv2.destroyAllWindows()