import cv2

camera = cv2.VideoCapture(0)

if not camera.isOpened():
    print("Error: Camera not opened.")
else:
    while True:
        ret, frame = camera.read()
        if not ret:
            print("Error: Failed to grab frame.")
            break
        
        # Show the frame in a window
        cv2.imshow("Camera Test", frame)
        
        # Break the loop on 'q' key press
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

camera.release()
cv2.destroyAllWindows()