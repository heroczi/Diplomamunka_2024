import socket
import cv2
import pygame
import numpy as np

# Initialize Pygame window
pygame.init()
window_size = (640, 480)
window = pygame.display.set_mode(window_size)
pygame.display.set_caption("Real-Time Video Stream")

# Initialize UDP socket for receiving video stream
recv_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
recv_sock.bind(("0.0.0.0", 5000))  # Bind to the port used by the server


def receive_video_stream():
    """Receive video stream from the server."""
    while True:
        data, _ = recv_sock.recvfrom(65507)  # Max UDP packet size

        # Convert the received data to a numpy array and decode it using OpenCV
        np_arr = np.frombuffer(data, np.uint8)
        frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

        if frame is not None:
            # Resize frame to fit Pygame window
            frame = cv2.resize(frame, window_size)

            # Convert the OpenCV image (BGR) to RGB for Pygame
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # Convert the image to a surface that Pygame can display
            pygame_surface = pygame.surfarray.make_surface(frame_rgb)

            # Blit the surface onto the Pygame window and update
            window.blit(pygame.transform.rotate(pygame_surface, -90), (0, 0))
            pygame.display.update()


if __name__ == "__main__":
    try:
        receive_video_stream()
    except KeyboardInterrupt:
        pass
    finally:
        recv_sock.close()
        send_sock.close()
        pygame.quit()