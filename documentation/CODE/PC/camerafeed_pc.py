import socket
import cv2
import numpy as np

# Socket setup
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect(('192.168.100.2', 6000))  # Connect to the Raspberry Pi's IP and port

try:
    while True:
        # Receive the size of the frame first (4 bytes)
        frame_size_data = client_socket.recv(4)
        frame_size = int.from_bytes(frame_size_data, byteorder='big')

        # Now receive the actual frame
        data = b''
        while len(data) < frame_size:
            packet = client_socket.recv(frame_size - len(data))
            if not packet:
                break
            data += packet

        # Convert the received bytes back into a numpy array and decode the JPEG
        frame = np.frombuffer(data, dtype=np.uint8)
        frame = cv2.imdecode(frame, cv2.IMREAD_COLOR)

        # Display the frame
        cv2.imshow('Video Stream', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

except Exception as e:
    print(f"Error: {e}")

finally:
    client_socket.close()
    cv2.destroyAllWindows()
