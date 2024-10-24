import socket
import struct
import numpy as np
import cv2
import pygame
import threading

# Raspberry Pi IP and port
RPI_IP = "192.168.100.2"
RPI_PORT_CONTROL = 9000  # Port for sending control commands
RPI_PORT_VIDEO = 2000     # Port for receiving video frames

CHUNK_SIZE =  65535   # Maximum size for UDP packets


def video_receiver():
    # Socket for receiving video feed
    sock_video = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock_video.bind(('0.0.0.0', RPI_PORT_VIDEO))  # Listen on all interfaces for video
    try:
        while True:
            try:
                # First, receive the frame size (packed as 4 bytes)
                packet, _ = sock_video.recvfrom(4)
                if len(packet) < 4:
                    print("Failed to receive frame size.")
                    continue

                # Unpack the frame size
                frame_size = struct.unpack(">I", packet)[0]
                print(f"Expected frame size: {frame_size}")

                # Now receive the actual frame data in chunks
                frame_data = b""
                while len(frame_data) < frame_size:
                    try:
                        packet, _ = sock_video.recvfrom(CHUNK_SIZE)
                        frame_data += packet
                    except socket.error as e:
                        print(f"Socket error while receiving frame data: {e}")
                        break  # Exit the loop if a socket error occurs

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
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                # Display the frame
                cv2.imshow('Video Stream', frame)

                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

            except (struct.error, socket.error) as e:
                # Handle specific known exceptions
                print(f"Error during frame processing: {e}")
                continue  # Continue to the next iteration of the loop

    except Exception as e:
        print(f"Unexpected error: {e}")

    cv2.destroyAllWindows()
    sock_video.close()



def control_sender():
    # Initialize pygame
    pygame.init()
    screen = pygame.display.set_mode((640, 480))
    pygame.event.set_grab(True)
    pygame.mouse.set_visible(False)

    # Control constants
    MOVE = 1
    SHOOT_START = 2
    SHOOT_STOP = 3 
    LASERTOGGLE = 4

    # Socket for sending control commands
    sock_control = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.MOUSEMOTION: # Mouse relative movement
                x_move, y_move = pygame.mouse.get_rel()
                data = f'{MOVE},{x_move},{y_move}'
                sock_control.sendto(data.encode(), (RPI_IP, RPI_PORT_CONTROL))

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left-click
                    data = f'{SHOOT_START},0,0'
                    sock_control.sendto(data.encode(), (RPI_IP, RPI_PORT_CONTROL))

            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:  # Left-click release
                    data = f'{SHOOT_STOP},0,0'
                    sock_control.sendto(data.encode(), (RPI_IP, RPI_PORT_CONTROL))

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_e:  # Toggle laser with 'E' key
                    data = f'{LASERTOGGLE},0,0'
                    sock_control.sendto(data.encode(), (RPI_IP, RPI_PORT_CONTROL))

                elif event.key == pygame.K_ESCAPE:  # Quit with 'Escape' key
                    running = False
    pygame.quit()
    sock_control.close()
# Clean up


def main():
    # # Start the video receiver in a separate thread
    video_thread = threading.Thread(target=video_receiver)
    video_thread.daemon = True
    video_thread.start()

    # Start the control sender
    control_sender()

if __name__ == "__main__":
    main()
