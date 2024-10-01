import socket
import struct
import numpy as np
import cv2

# Initialize the UDP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(('0.0.0.0', 8000))  # Listen on all interfaces on port 8000

CHUNK_SIZE = 65507  # Maximum size for UDP packets
try:
    while True:
        # First, receive the frame size (packed as 4 bytes)
        packet, _ = sock.recvfrom(4)
        if len(packet) < 4:
            print("Failed to receive frame size.")
            continue

        # Unpack the frame size
        frame_size = struct.unpack(">I", packet)[0]
        print(f"Expected frame size: {frame_size}")

        # Now receive the actual frame data in chunks
        frame_data = b""
        while len(frame_data) < frame_size:
            packet, _ = sock.recvfrom(CHUNK_SIZE)
            frame_data += packet

        # Check if we received the expected amount of data
        if len(frame_data) != frame_size:
            print(f"Warning: Expected frame data size: {frame_size}, but got: {len(frame_data)}")
            continue

        # Decode the JPEG frame
        frame_array = np.frombuffer(frame_data, np.uint8)
        frame = cv2.imdecode(frame_array, cv2.IMREAD_COLOR)

        # Check if frame is successfully decoded
        if frame is None or frame.size == 0:
            print("Failed to decode frame.")
            continue


        # Convert from BGR to RGB if necessary (only if using RGB format for encoding)
        # Comment this out if your source is already BGR
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Display the frame
        cv2.imshow('Video Stream', frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

except Exception as e:
    print(f"Error: {e}")

finally:
    sock.close()
    cv2.destroyAllWindows()