import cv2
import numpy as np
import gpiozero
from picamera2 import Picamera2
from DRV8825 import DRV8825

# Setup camera
camera = Picamera2()
camera.configure(camera.create_preview_configuration(main={"size": (640, 480)}))
camera.start()

# Setup motors
Motor1 = DRV8825(dir_pin=13, step_pin=19, enable_pin=12)
Motor2 = DRV8825(dir_pin=24, step_pin=18, enable_pin=4)

cascade_path = 'haarcascade_frontalface_default.xml'
# Face detection setup
face_cascade = cv2.CascadeClassifier(cascade_path)

def move_camera(x, y, frame_center_x, frame_center_y):
    pan_error = frame_center_x - x
    tilt_error = frame_center_y - y

    # Adjust motor speed based on error
    if abs(pan_error) > 20:  # tolerance range
        dirx = 1 if pan_error > 0 else -1
        Motor1.TurnStep(dirx, 1, stepdelay=0)

    # else:
    #     pan_motor.stop()

    if abs(tilt_error) > 20:  # tolerance range
        dirx = 1 if tilt_error > 0 else -1
        Motor2.TurnStep(dirx, 1, stepdelay=0)
    # else:
    #     tilt_motor.stop()

while True:
    frame = camera.capture_array()
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    # Detect faces
    faces = face_cascade.detectMultiScale(gray, 1.3, 5)
    
    frame_center_x = frame.shape[1] // 2
    frame_center_y = frame.shape[0] // 2

    if len(faces) > 0:
        # Assume the first face is the target
        (x, y, w, h) = faces[0]
        face_center_x = x + w // 2
        face_center_y = y + h // 2
        
        # Move the camera
        move_camera(face_center_x, face_center_y, frame_center_x, frame_center_y)
        
        # Draw a rectangle around the face
        cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)
    
    # # Optionally display the frame locally
    # cv2.imshow('Camera Feed', frame)
    # if cv2.waitKey(1) & 0xFF == ord('q'):
    #     break

# Clean up
cv2.destroyAllWindows()
camera.stop()