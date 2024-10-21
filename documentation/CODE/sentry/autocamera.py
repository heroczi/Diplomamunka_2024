import cv2
import socket
import pickle
import struct
from picamera2 import Picamera2

# Set up camera
camera = Picamera2()
camera.configure(camera.create_preview_configuration(main={"size": (640, 480)}))
camera.start()

# Set up socket
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind(('0.0.0.0', 7000))  # Change port if necessary
server_socket.listen(1)

conn, addr = server_socket.accept()
print(f"Connection established with {addr}")

# Load the Haar Cascade for face detection
face_cascade = cv2.CascadeClassifier('/path/to/haarcascade_frontalface_default.xml')

while True:
    # Capture frame
    frame = camera.capture_array()
    
    # Convert frame to grayscale for face detection
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    # Detect faces
    faces = face_cascade.detectMultiScale(gray, 1.3, 5)
    
    # Draw rectangle around the faces
    for (x, y, w, h) in faces:
        cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)
    
    # Serialize the frame (convert it to a byte stream)
    data = pickle.dumps(frame)
    message_size = struct.pack("L", len(data))  # Pack the frame size
    
    # Send the frame size and the frame
    conn.sendall(message_size + data)

# Cleanup (this part will only be executed when the connection ends)
conn.close()
server_socket.close()