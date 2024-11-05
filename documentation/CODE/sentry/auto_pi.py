import cv2
import numpy as np
import pickle 
import socket
import struct


PC_IP = "192.168.100.1"  # PC's IP address
RPI_IP = "192.168.100.2"
RPI_PORT_CONTROL = 9000  # Port for receiving control commands
RPI_PORT_VIDEO = 2000     # Port for sending video frames

server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 65536)

# Load the template image (your "Z" pattern) and initialize ORB
template = cv2.imread('target.png', cv2.IMREAD_GRAYSCALE)
orb = cv2.ORB_create()

# Detect keypoints and descriptors in the template image
keypoints_template, descriptors_template = orb.detectAndCompute(template, None)

# Initialize video capture for the Pi camera
cap = cv2.VideoCapture(0, cv2.CAP_V4L2)  # or use cv2.VideoCapture(0) for the Pi Camera Module

# Define the Matcher
bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)

# Function to find the template and track its position
def track_template(frame):
    # Convert frame to grayscale
    gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    # Detect keypoints and descriptors in the current frame
    keypoints_frame, descriptors_frame = orb.detectAndCompute(gray_frame, None)

    if descriptors_template is None or descriptors_frame is None:
        return None, None

    # Match descriptors
    matches = bf.match(descriptors_template, descriptors_frame)
    matches = sorted(matches, key=lambda x: x.distance)

    # Minimum number of matches to consider a valid detection
    min_matches = 10
    if len(matches) > min_matches:
        # Extract location of good matches
        src_pts = np.float32([keypoints_template[m.queryIdx].pt for m in matches]).reshape(-1, 1, 2)
        dst_pts = np.float32([keypoints_frame[m.trainIdx].pt for m in matches]).reshape(-1, 1, 2)

        # Find homography matrix to align template and frame
        M, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)

        if M is not None:
            # Get dimensions of the template image
            h, w = template.shape

            # Get the coordinates of the template corners in the current frame
            template_corners = np.float32([[0, 0], [w, 0], [w, h], [0, h]]).reshape(-1, 1, 2)
            transformed_corners = cv2.perspectiveTransform(template_corners, M)

            # Calculate the center of the detected template
            center_x = np.mean(transformed_corners[:, 0, 0])
            center_y = np.mean(transformed_corners[:, 0, 1])

            # Calculate offset from the center of the frame
            frame_center_x = gray_frame.shape[1] / 2
            frame_center_y = gray_frame.shape[0] / 2
            offset_x = center_x - frame_center_x
            offset_y = center_y - frame_center_y

            # Draw bounding box and center point for visualization
            frame = cv2.polylines(frame, [np.int32(transformed_corners)], True, (0, 255, 0), 3, cv2.LINE_AA)
            cv2.circle(frame, (int(center_x), int(center_y)), 5, (0, 0, 255), -1)

            MAX_DGRAM = 65000  # Max datagram size, less than 65507 to allow for headers
            packet_id = 0

            encoded, buffer = cv2.imencode('.jpg', frame)
            data = pickle.dumps(buffer)
        
            # Split data into chunks
            chunks = [data[i:i + MAX_DGRAM] for i in range(0, len(data), MAX_DGRAM)]

            for i, chunk in enumerate(chunks):
            # Create a header with packet_id, chunk index, and total number of chunks
                header = struct.pack("!HHH", packet_id, i, len(chunks))
                packet = header + chunk
                server_socket.sendto(packet, (PC_IP, RPI_PORT_VIDEO))

            # Increment packet ID to help the receiver with reassembly
            packet_id = (packet_id + 1) % 65535


            # Print or return offset to track movement
            print(f"Offset X: {offset_x}, Offset Y: {offset_y}")
            return offset_x, offset_y

    return None, None

MAX_DGRAM = 65000
# Main loop to capture frames and track the template
while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break
    
    # Track the template in the current frame
    offset_x, offset_y = track_template(frame)


# Release resources
cap.release()
cv2.destroyAllWindows()