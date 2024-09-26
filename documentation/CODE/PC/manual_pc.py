import socket
import pygame

# Raspberry Pi IP and port
RPI_IP = "192.168.100.2"
RPI_PORT = 5000

# Initialize pygame for keyboard input
pygame.init()
screen = pygame.display.set_mode((1920, 1080))

# Socket setup
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)


running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        else:
            pos = pygame.mouse.get_rel()
            print(pos)
            data = f'{pos[0]},{pos[1]}'
            sock.sendto(data.encode(), (RPI_IP, RPI_PORT))

pygame.quit()
sock.close()