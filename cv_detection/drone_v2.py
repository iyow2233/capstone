import cv2
from ultralytics import YOLO
from picamezro import camera  # Assuming this is correct for your setup
import time

# Initialize the Raspberry Pi Camera
cam = camera.Camera()  # Replace with correct initialization if needed
cam.resolution = (640, 480)
cam.framerate = 30

# Load YOLO model (Use a small, efficient model for Raspberry Pi)
model = YOLO('yolo11n.pt')  # Ensure the model is optimized for edge devices

while True:
    # Capture frame from Raspberry Pi Camera
    frame = cam.capture()  # Assuming `capture()` gives a NumPy array
    
    if frame is None:
        continue  # Skip frame if capture fails

    # Perform YOLO drone detection
    results = model.predict(frame)

    for result in results:
        boxes = result.boxes
        for box in boxes:
            x1, y1, x2, y2 = box.xyxy[0]
            x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)

            # Draw bounding box around detected drone
            color = (0, 255, 0)  # Green bounding box
            thickness = 2
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, thickness)

            # Add label text
            label = "Drone Detected"
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 0.6
            text_thickness = 2
            cv2.putText(frame, label, (x1, y1 - 10), font, font_scale, color, text_thickness)

    # Display the output
    cv2.imshow("Drone Detection", frame)
    
    if cv2.waitKey(1) & 0xFF == ord('q'):  # Press 'q' to exit
        break

cv2.destroyAllWindows()
cam.close()
