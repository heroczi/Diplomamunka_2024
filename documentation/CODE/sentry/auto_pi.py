import cv2
import numpy as np
from picamera2 import Picamera2

# Load the template image (symbol) and convert it to grayscale
template = cv2.imread('target.png', cv2.IMREAD_GRAYSCALE)
template_h, template_w = template.shape[:2]

# Set up the Pi camera
camera = cv2.VideoCapture(0, cv2.CAP_V4L2)
camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

while True:
    # Capture frame from the camera
    ret, frame = camera.read()
    gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    # Perform template matching
    result = cv2.matchTemplate(gray_frame, template, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(result)

    # Define a threshold for detection certainty (tweak as needed)
    threshold = 0.4
    if max_val >= threshold:
        # Get the top-left corner of the matched region
        top_left = max_loc
        bottom_right = (top_left[0] + template_w, top_left[1] + template_h)

        # Draw a rectangle around the detected symbol
        cv2.rectangle(frame, top_left, bottom_right, (0, 255, 0), 2)
        print(f"Symbol found at: {top_left}")

    # Display frame with the matched symbol (for testing; comment out if headless)
    cv2.imshow("Symbol Detection", frame)

    # Press 'q' to exit
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

camera.stop()
cv2.destroyAllWindows()