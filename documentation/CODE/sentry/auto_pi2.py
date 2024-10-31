import cv2
import numpy as np


camera = cv2.VideoCapture(0, cv2.CAP_V4L2)
camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

def capture_frame():
    # Capture a frame from the Raspberry Pi camera
    ret, frame = camera.read()
    return frame

def load_template(template_path):
    # Load the template image in grayscale
    template = cv2.imread(template_path, 0)
    if template is None:
        raise ValueError(f"Template image at {template_path} could not be loaded.")
    return template

def find_and_track_template(frame, template):
    # Convert the frame to grayscale
    gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Get dimensions of the template
    template_height, template_width = template.shape[:2]

    # Perform template matching
    result = cv2.matchTemplate(gray_frame, template, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

    # Set a threshold for matching; adjust based on your template
    threshold = 0.7  # A match value close to 1.0 indicates a high match
    if max_val >= threshold:
        # Draw a rectangle around the detected area
        top_left = max_loc
        bottom_right = (top_left[0] + template_width, top_left[1] + template_height)
        cv2.rectangle(frame, top_left, bottom_right, (0, 255, 0), 2)

        # Calculate the center of the detected template
        cx = top_left[0] + template_width // 2
        cy = top_left[1] + template_height // 2

        # Mark the center
        cv2.circle(frame, (cx, cy), 5, (0, 0, 255), -1)

        # Return the center coordinates for tracking
        return cx, cy, frame

    # Return None if the template is not found
    return None, None, frame

def main(template_path):

    template = load_template(template_path)
    
    try:
        while True:
            # Capture frame from the camera
            frame = capture_frame()

            # Find and track the template
            cx, cy, output_frame = find_and_track_template(frame, template)

            # Display the tracking result
            cv2.imshow("Template Tracker", output_frame)

            if cx is not None and cy is not None:
                print(f"Template detected at position: X={cx}, Y={cy}")
            else:
                print("Template not found")

            # Exit loop when 'q' is pressed
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    finally:
        # Clean up
        camera.stop()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    # Replace "path_to_template.png" with the path to your template image
    main("target.png")
