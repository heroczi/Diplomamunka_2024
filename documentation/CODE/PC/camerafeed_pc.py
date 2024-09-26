import socket
import cv2
import pickle
import struct

# Create a TCP/IP socket
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Connect to the Raspberry Pi server
server_ip = '192.168.100.2'  # Use the Raspberry Pi's IP address
port = 8000
client_socket.connect((server_ip, port))

# Buffer size
data = b""
payload_size = struct.calcsize("L")  # Size of unsigned long (the frame size)

while True:
    # Retrieve the size of the frame
    while len(data) < payload_size:
        packet = client_socket.recv(4096)  # Receive data in chunks
        if not packet:
            break
        data += packet

    packed_msg_size = data[:payload_size]
    data = data[payload_size:]
    msg_size = struct.unpack("L", packed_msg_size)[0]  # Unpack the frame size

    # Retrieve the actual frame data based on the size
    while len(data) < msg_size:
        data += client_socket.recv(4096)

    frame_data = data[:msg_size]
    data = data[msg_size:]

    # Deserialize the frame
    frame = pickle.loads(frame_data)

    # Decode the JPEG back into an image
    frame = cv2.imdecode(frame, cv2.IMREAD_COLOR)

    # Display the frame
    cv2.imshow('Video Stream', frame)

    # Exit if the user presses 'q'
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

client_socket.close()
cv2.destroyAllWindows()