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

def video_receiver(stop_event, frame_queue):
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
                frame_queue.put(frame)
            # Clear buffer for the next frame
            buffer = {}

        cv2.waitKey(1)
        
    video_socket.close()
    cv2.destroyAllWindows()
    print("Video process terminated.")

def control_sender(stop_event,frame_queue):
    print("Control sender process started.")
    
    sock_control = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    pygame.init()
    screen = pygame.display.set_mode((640, 480))
    pygame.event.set_grab(True)
    pygame.mouse.set_visible(False)
    
    # Define fonts and colors
    font = pygame.font.Font(None, 24)
    white = (255, 255, 255)
    red = (255, 0, 0)
    green = (0, 255, 0)
    black = (0, 0, 0)
    
    # Initial states
    laser_on = False
    safety_on = True
    mode = "Manual"

    # Command constants
    MOVE = 1
    SHOOT_START = 2
    SHOOT_STOP = 3
    LASERTOGGLE = 4
    SAFETY = 5
    MANUALMODE = 6
    AUTOMODE = 7
    STOP = 9

    # Main loop
    while not stop_event.is_set():
        # Get the latest frame from the queue if available
        while not frame_queue.empty():
            last_frame = frame_queue.get()  # Keep only the latest frame

        # If we have a frame, use it; otherwise, use a black background
        if last_frame is not None:
            # Convert the frame from BGR (OpenCV) to RGB (pygame)
            frame_rgb = cv2.cvtColor(last_frame, cv2.COLOR_BGR2RGB)
            frame_rgb = cv2.flip(frame_rgb, 1)  # Flip horizontally
            # Convert the frame to a pygame surface
            frame_surface = pygame.surfarray.make_surface(np.rot90(frame_rgb))
            # Scale the frame to fit the pygame window if needed
            frame_surface = pygame.transform.scale(frame_surface, (640, 480))
            # Blit the frame onto the screen
            screen.blit(frame_surface, (0, 0))
        else:
            # No frame available; fill with black background
            screen.fill((0, 0, 0))

        # Display the control instructions
        instructions = [
            "Controls:",
            "1 - Manual Mode",
            "2 - Auto Mode",
            "L - Toggle Laser",
            "S - Toggle Safety",
            "Esc - Stop Program",
            "Left Mouse Button - Shoot",
            "Mouse Movement - Move",
        ]
        
        # Render the instructions on the screen
        for i, line in enumerate(instructions):
            text_surface = font.render(line, True, white)
            screen.blit(text_surface, (10, 10 + i * 20))

        # Display the status indicators
        status_texts = [
            f"Mode: {mode}",
            f"Laser: {'On' if laser_on else 'Off'}",
            f"Safety: {'On' if safety_on else 'Off'}"
        ]
        
        # Render the status indicators on the screen
        for i, line in enumerate(status_texts):
            color = green if "On" in line else red  # Green if "On", red if "Off"
            text_surface = font.render(line, True, color)
            screen.blit(text_surface, (10, 200 + i * 20))

        pygame.display.flip()  # Update the display

        # Handle events
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

                if event.key == pygame.K_ESCAPE:
                    data = f'{STOP},0,0'
                    sock_control.sendto(data.encode(), (RPI_IP, RPI_PORT_CONTROL))
                    stop_event.set()
                    pygame.time.delay(100)

                elif event.key == pygame.K_1:
                    mode = "Manual"
                    data = f'{MANUALMODE},0,0'
                    sock_control.sendto(data.encode(), (RPI_IP, RPI_PORT_CONTROL))
                
                elif event.key == pygame.K_2:
                    mode = "Auto"
                    data = f'{AUTOMODE},0,0'
                    sock_control.sendto(data.encode(), (RPI_IP, RPI_PORT_CONTROL))

                elif event.key == pygame.K_l:
                    laser_on = not laser_on
                    data = f'{LASERTOGGLE},0,0'
                    sock_control.sendto(data.encode(), (RPI_IP, RPI_PORT_CONTROL))

                elif event.key == pygame.K_s:
                    safety_on = not safety_on
                    data = f'{SAFETY},0,0'
                    sock_control.sendto(data.encode(), (RPI_IP, RPI_PORT_CONTROL))

    pygame.quit()
    sock_control.close()
    print("Control sender process terminated.")


def main():
    stop_event = multiprocessing.Event()

    frame_queue = multiprocessing.Queue()
    
    video_process = multiprocessing.Process(target=video_receiver, args=(stop_event,frame_queue,))
    control_process = multiprocessing.Process(target=control_sender, args=(stop_event,frame_queue,))

    video_process.start()
    control_process.start()

    # Wait for both processes to finish
    video_process.join()
    control_process.join()

    frame_queue.close()
    frame_queue.join_thread()
    print("All processes terminated.")

if __name__ == "__main__":
    main()

