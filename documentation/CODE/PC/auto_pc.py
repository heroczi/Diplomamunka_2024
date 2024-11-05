import multiprocessing
import socket
import cv2
import numpy as np
import pickle

import struct


# Raspberry Pi IP and ports
RPI_IP = "192.168.100.2"
RPI_PORT_CONTROL = 9000  # Port for sending control commands
RPI_PORT_VIDEO = 2000     # Port for receiving video frames

def video_receiver(stop_event):
    print("Video process started.")
    video_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    video_socket.bind(('0.0.0.0', RPI_PORT_VIDEO))

    MAX_DGRAM = 65000  # Max datagram size
    buffer = {}
    packet_id_last = -1

    while True:
        packet, _ = video_socket.recvfrom(MAX_DGRAM + 6)  # Additional bytes for header
        header = packet[:6]
        packet_id, chunk_index, total_chunks = struct.unpack("!HHH", header)
        chunk_data = packet[6:]

        if packet_id != packet_id_last:
            buffer = {}  # Clear buffer if a new packet ID is received
            packet_id_last = packet_id

        # Collect chunks in buffer based on packet ID
        buffer[chunk_index] = chunk_data

        # Reassemble if all chunks are received
        print("pina")
        if len(buffer) == total_chunks:
            data = b"".join([buffer[i] for i in range(total_chunks)])
            frame = pickle.loads(data)
            frame = cv2.imdecode(frame, cv2.IMREAD_COLOR)
            print("fasz")
            if frame is not None:
                print("segg")
                cv2.imshow("DESTROY", frame)

            # Clear buffer for the next frame
            buffer = {}

        cv2.waitKey(1)
        
    video_socket.close()
    cv2.destroyAllWindows()
    print("Video process terminated.")

def main():
    stop_event = multiprocessing.Event()
    
    video_process = multiprocessing.Process(target=video_receiver, args=(stop_event,))
    # control_process = multiprocessing.Process(target=control_sender, args=(stop_event,))

    video_process.start()
    # control_process.start()

    # Wait for both processes to finish
    video_process.join()
    # control_process.join()
    print("All processes terminated.")

if __name__ == "__main__":
    main()