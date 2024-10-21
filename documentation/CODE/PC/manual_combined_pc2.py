import multiprocessing
import socket
import cv2
import numpy as np
import struct
import pygame

# Raspberry Pi IP and ports
RPI_IP = "192.168.100.2"
RPI_PORT_CONTROL = 9000  # Port for sending control commands
RPI_PORT_VIDEO = 2000     # Port for receiving video frames

CHUNK_SIZE = 65507  # Maximum size for UDP packets

def video_receiver():
    print("Video receiver process started.")
    
    sock_video = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock_video.bind(('0.0.0.0', RPI_PORT_VIDEO))  # Only bind for video receiver
    
    print("Socket for video receiver bound to port", RPI_PORT_VIDEO)
    
    while True:
        try:
            # Receive and handle video frames here
            packet, _ = sock_video.recvfrom(4)
            print("Received packet size")
            
            if len(packet) < 4:
                print("Failed to receive frame size.")
                continue

            frame_size = struct.unpack(">I", packet)[0]
            print(f"Expected frame size: {frame_size}")

            frame_data = b""
            while len(frame_data) < frame_size:
                packet, _ = sock_video.recvfrom(CHUNK_SIZE)
                frame_data += packet

            if len(frame_data) != frame_size:
                print(f"Warning: Expected frame data size: {frame_size}, but got: {len(frame_data)}")
                continue

            # Convert the frame data into an image
            frame_array = np.frombuffer(frame_data, np.uint8)
            frame = cv2.imdecode(frame_array, cv2.IMREAD_COLOR)
            if frame is None or frame.size == 0:
                print("Failed to decode frame.")
                continue

            # Show the image in a window
            cv2.imshow('Video Stream', frame)
            print("Displaying frame.")
            
            # Close the window if 'q' is pressed
            if cv2.waitKey(1) & 0xFF == ord('q'):
                print("Exit key pressed. Closing video stream.")
                break

        except Exception as e:
            print(f"Error in video receiver: {e}")

    sock_video.close()
    cv2.destroyAllWindows()

def control_sender():
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

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.MOUSEMOTION:
                x_move, y_move = pygame.mouse.get_rel()
                data = f'{MOVE},{x_move},{y_move}'
                sock_control.sendto(data.encode(), (RPI_IP, RPI_PORT_CONTROL))
                print(f"Sent movement data: {data}")

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    data = f'{SHOOT_START},0,0'
                    sock_control.sendto(data.encode(), (RPI_IP, RPI_PORT_CONTROL))
                    print(f"Sent shoot start command: {data}")

            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    data = f'{SHOOT_STOP},0,0'
                    sock_control.sendto(data.encode(), (RPI_IP, RPI_PORT_CONTROL))
                    print(f"Sent shoot stop command: {data}")

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_e:
                    data = f'{LASERTOGGLE},0,0'
                    sock_control.sendto(data.encode(), (RPI_IP, RPI_PORT_CONTROL))
                    print(f"Sent laser toggle command: {data}")

                elif event.key == pygame.K_ESCAPE:
                    running = False
                    print("Escape key pressed. Exiting control sender.")

    sock_control.close()
    pygame.quit()

def main():
    # Create separate processes for video receiving and control sending
    video_process = multiprocessing.Process(target=video_receiver)
    control_process = multiprocessing.Process(target=control_sender)

    # Start the processes
    video_process.start()
    control_process.start()

    # Wait for both processes to finish
    video_process.join()
    control_process.join()

if __name__ == "__main__":
    main()
