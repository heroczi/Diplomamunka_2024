import multiprocessing
import socket
import cv2
import numpy as np
import pickle
import pygame
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

    while not stop_event.is_set():
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
        if len(buffer) == total_chunks:
            data = b"".join([buffer[i] for i in range(total_chunks)])
            frame = pickle.loads(data)
            frame = cv2.imdecode(frame, cv2.IMREAD_COLOR)
            if frame is not None:
                cv2.imshow("DESTROY", frame)

            # Clear buffer for the next frame
            buffer = {}

        cv2.waitKey(1)
        
    video_socket.close()
    cv2.destroyAllWindows()
    print("Video process terminated.")

def control_sender(stop_event):
    print("Control sender process started.")
    
    sock_control = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    pygame.init()
    screen = pygame.display.set_mode((640, 480))
    pygame.event.set_grab(True)
    pygame.mouse.set_visible(False)

    MOVE = 1
    SHOOT_START = 2
    SHOOT_STOP = 3
    LASERTOGGLE = 4

    STOP = 9

    while not stop_event.is_set():
        for event in pygame.event.get():
            if event.type == pygame.MOUSEMOTION:
                x_move, y_move = pygame.mouse.get_rel()
                data = f'{MOVE},{x_move},{y_move}'
                sock_control.sendto(data.encode(), (RPI_IP, RPI_PORT_CONTROL))
            
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    data = f'{SHOOT_START},0,0'
                    sock_control.sendto(data.encode(), (RPI_IP, RPI_PORT_CONTROL))

            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    data = f'{SHOOT_STOP},0,0'
                    sock_control.sendto(data.encode(), (RPI_IP, RPI_PORT_CONTROL))

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_e:
                    data = f'{LASERTOGGLE},0,0'
                    sock_control.sendto(data.encode(), (RPI_IP, RPI_PORT_CONTROL))
                elif event.key == pygame.K_ESCAPE:
                    data = f'{STOP},0,0'
                    sock_control.sendto(data.encode(), (RPI_IP, RPI_PORT_CONTROL))
                    stop_event.set()

    pygame.quit()
    sock_control.close()
    print("Control sender process terminated.")

def main():
    stop_event = multiprocessing.Event()
    
    video_process = multiprocessing.Process(target=video_receiver, args=(stop_event,))
    control_process = multiprocessing.Process(target=control_sender, args=(stop_event,))

    video_process.start()
    control_process.start()

    # Wait for both processes to finish
    video_process.join()
    control_process.join()
    print("All processes terminated.")

if __name__ == "__main__":
    main()

