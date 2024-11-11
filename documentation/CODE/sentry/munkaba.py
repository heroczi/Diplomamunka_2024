import cv2
import numpy as np

# Load the template image (symbol) and convert it to grayscale
template = cv2.imread('target.png', cv2.IMREAD_GRAYSCALE)
if template is None:
    raise ValueError("Template image not found.")

# Initialize ORB detector
orb = cv2.ORB_create()

# Detect keypoints and descriptors in the template image
keypoints_template, descriptors_template = orb.detectAndCompute(template, None)

# Set up the camera
camera = cv2.VideoCapture(0, cv2.CAP_V4L2)
camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

# Initialize a matcher for matching keypoints
matcher = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)

# Tracking variables
tracking = False
tracker = None

while True:
    # Capture frame from the camera
    ret, frame = camera.read()
    if not ret:
        break
    
    # Convert frame to grayscale
    gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    if not tracking:
        # Detection phase: Detect keypoints and descriptors in the current frame
        keypoints_frame, descriptors_frame = orb.detectAndCompute(gray_frame, None)
        
        # Match descriptors between template and frame
        matches = matcher.match(descriptors_template, descriptors_frame)
        
        # Sort matches by distance (best matches first)
        matches = sorted(matches, key=lambda x: x.distance)
        
        # Filter good matches based on distance (tune the number if needed)
        good_matches = matches[:10]  # Consider top 10 matches
        
        # Check if enough good matches are found to consider detection
        if len(good_matches) >= 8:  # Adjust threshold as needed
            # Extract matched keypoints
            src_pts = np.float32([keypoints_template[m.queryIdx].pt for m in good_matches]).reshape(-1, 1, 2)
            dst_pts = np.float32([keypoints_frame[m.trainIdx].pt for m in good_matches]).reshape(-1, 1, 2)
            
            # Compute homography if enough matches found
            M, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)
            
            if M is not None:
                # Get the bounding box points for the template image
                h, w = template.shape
                pts = np.float32([[0, 0], [w, 0], [w, h], [0, h]]).reshape(-1, 1, 2)
                dst = cv2.perspectiveTransform(pts, M)
                
                # Draw bounding box in the frame
                frame = cv2.polylines(frame, [np.int32(dst)], True, (255, 0, 0), 3, cv2.LINE_AA)
                
                # Initialize a tracker on the detected region
                bbox = cv2.boundingRect(dst)
                tracker = cv2.TrackerCSRT_create()  # Choose preferred tracker
                tracker.init(frame, bbox)
                tracking = True
                print("Tracking started.")
    
    else:
        # Tracking phase: Update tracker if object is being tracked
        ok, bbox = tracker.update(frame)

        if ok:
            # Tracking successful, draw bounding box
            p1 = (int(bbox[0]), int(bbox[1]))
            p2 = (int(bbox[0] + bbox[2]), int(bbox[1] + bbox[3]))
            cv2.rectangle(frame, p1, p2, (255, 0, 0), 2, 1)
        else:
            # Tracking failure (object likely out of frame)
            print("Tracking lost. Resuming detection.")
            tracking = False  # Go back to detection phase
            tracker = None  # Reset tracker
    
    # Display frame with detection or tracking result
    cv2.imshow("Symbol Tracking", frame)

    # Press 'q' to exit
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

camera.release()
cv2.destroyAllWindows()
