import socket
import pygame

# Raspberry Pi IP and port
RPI_IP = "192.168.100.2"
RPI_PORT = 5000

MOVE = 1
SHOOT_START = 2
SHOOT_STOP = 3  # Corrected, SHOOT_STOP should be a different event type
LASERTOGGLE = 4


# Initialize pygame
pygame.init()
screen = pygame.display.set_mode((640, 480))
pygame.event.set_grab(True)
pygame.mouse.set_visible(False)

# Socket setup
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.settimeout(5)  # Add a timeout for socket operations

# Function to send data to Raspberry Pi
def send_data(eventtype, move):
    try:
        data = f'{eventtype},{move[0]},{move[1]}'
        sock.sendto(data.encode(), (RPI_IP, RPI_PORT))
    except socket.error as e:
        print(f"Socket error: {e}")
        return False
    return True

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False  # Exit if ESC is pressed

            elif event.key == pygame.K_q:
                move = pygame.mouse.get_rel()
                if not send_data(LASERTOGGLE, move):
                    running = False


        elif event.type == pygame.MOUSEMOTION:
            move = pygame.mouse.get_rel()
            if not send_data(MOVE, move):
                running = False

        elif event.type == pygame.MOUSEBUTTONDOWN:
            move = pygame.mouse.get_rel()
            if not send_data(SHOOT_START, move):
                running = False

        elif event.type == pygame.MOUSEBUTTONUP:
            move = pygame.mouse.get_rel()
            if not send_data(SHOOT_STOP, move):
                running = False

# Clean up
pygame.quit()
sock.close()