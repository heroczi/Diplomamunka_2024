import socket
import pygame

# Raspberry Pi IP and port
RPI_IP = "192.168.100.2"
RPI_PORT = 5000

# Initialize pygame
pygame.init()
screen = pygame.display.set_mode((640, 480))
pygame.event.set_grab(True)
pygame.mouse.set_visible(False)

# Socket setup
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)


running = True
while running:
    for event in pygame.event.get():

        if event.type == pygame.MOUSEMOTION:
            move = pygame.mouse.get_rel()
            print(move)
            data = f'{move[0]},{move[1]}'
            sock.sendto(data.encode(), (RPI_IP, RPI_PORT))

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                data = f'{0},{0}'
                sock.sendto(data.encode(), (RPI_IP, RPI_PORT))
            if event.key == pygame.K_e:
                data = f'{0},{0}'
                sock.sendto(data.encode(), (RPI_IP, RPI_PORT))

        if event.type == pygame.QUIT:
            running = False


        
        



pygame.quit()
sock.close() 