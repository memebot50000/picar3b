import cv2
import numpy as np
import time
import subprocess
import io
from PIL import Image

# Function to capture a frame using rpicam-still
def capture_frame():
    result = subprocess.run(['rpicam-still', '-n', '-o', '-', '-t', '1', '--width', '640', '--height', '480'], capture_output=True)
    image = Image.open(io.BytesIO(result.stdout))
    return cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

def main():
    # Initialize variables for odometry
    prev_frame = None
    x, y = 0, 0  # Starting position
    heading = 0

    # Starting GPS position (36 Cummings Rd, Newton, MA)
    lat, lon = 42.3300, -71.2089

    print("Visual Odometry Started")
    print("Press Ctrl+C to stop")

    try:
        while True:
            image = capture_frame()

            if prev_frame is None:
                prev_frame = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                continue

            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

            # Calculate optical flow
            flow = cv2.calcOpticalFlowFarneback(prev_frame, gray, None, 0.5, 3, 15, 3, 5, 1.2, 0)

            # Calculate movement
            h, w = flow.shape[:2]
            fx, fy = flow[h//2, w//2]
            
            # Update position (very simplified, you might need to calibrate this)
            scale = 0.1  # This scale factor needs to be calibrated
            x += fx * scale
            y += fy * scale

            # Update heading (simplified)
            heading = np.arctan2(fy, fx)

            # Update GPS position (very simplified, you need to calibrate this)
            lat += y * 1e-7  # Approximate conversion, needs calibration
            lon += x * 1e-7  # Approximate conversion, needs calibration

            # Update previous frame
            prev_frame = gray

            # Print current position and GPS coordinates
            print(f"Position: ({x:.2f}, {y:.2f}), Heading: {heading:.2f}")
            print(f"GPS: Lat: {lat:.7f}, Lon: {lon:.7f}")

            # Add a small delay
            time.sleep(0.1)

    except KeyboardInterrupt:
        print("\nProgram interrupted by user. Exiting...")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        print("Visual Odometry Stopped")

if __name__ == "__main__":
    main()
