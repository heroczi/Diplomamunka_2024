import pygame
import sys

# Initialize pygame
pygame.init()

# Set up window
screen = pygame.display.set_mode((800, 600))

# Set grabbing of the input and hide the cursor
pygame.event.set_grab(True)
pygame.mouse.set_visible(False)

# Main loop
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    # Get relative mouse movement
    rel_x, rel_y = pygame.mouse.get_rel()

    # Use rel_x and rel_y to control stepper motors, for example
    print(f"Relative movement: {rel_x}, {rel_y}")

    # Clear the screen
    screen.fill((0, 0, 0))

    # Update the display
    pygame.display.flip()

    # Control the frame rate
    pygame.time.Clock().tick(60)