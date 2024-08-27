import cv2
import numpy as np
import time
import subprocess
import io
from PIL import Image
from collections import deque

# Function to capture a frame using rpicam-still
def capture_frame():
    result = subprocess.run(['rpicam-still', '-n', '-o', '-', '-t', '1', '--width', '640', '--height', '480'], capture_output=True)
    image = Image.open(io.BytesIO(result.stdout))
    return cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

def calculate_average_flow(flow):
    h, w = flow.shape[:2]
    fx, fy = flow[h//4:3*h//4, w//4:3*w//4].mean(axis=(0, 1))
    return fx, fy

def main():
    # Initialize variables for odometry
    prev_frame = None
    x, y = 0, 0  # Starting position
    heading = 0

    # Starting GPS position (36 Cummings Rd, Newton, MA)
    lat, lon = 42.3300, -71.2089

    # Parameters for tuning
    scale = 0.001  # This scale factor needs to be calibrated
    smoothing_window = 5
    x_smooth = deque([0] * smoothing_window, maxlen=smoothing_window)
    y_smooth = deque([0] * smoothing_window, maxlen=smoothing_window)

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
            flow = cv2.calcOpticalFlowFarneback(prev_frame, gray, None, 0.5, 5, 15, 3, 5, 1.2, 0)

            # Calculate average movement
            fx, fy = calculate_average_flow(flow)
            
            # Update position with smoothing
            x += fx * scale
            y += fy * scale
            x_smooth.append(x)
            y_smooth.append(y)
            x_smoothed = sum(x_smooth) / smoothing_window
            y_smoothed = sum(y_smooth) / smoothing_window

            # Update heading (simplified)
            heading = np.arctan2(fy, fx)

            # Update GPS position (very simplified, you need to calibrate this)
            lat += y_smoothed * 1e-7  # Approximate conversion, needs calibration
            lon += x_smoothed * 1e-7  # Approximate conversion, needs calibration

            # Update previous frame
            prev_frame = gray

            # Print current position and GPS coordinates
            print(f"Raw Position: ({x:.4f}, {y:.4f})")
            print(f"Smoothed Position: ({x_smoothed:.4f}, {y_smoothed:.4f})")
            print(f"Heading: {heading:.2f}")
            print(f"GPS: Lat: {lat:.7f}, Lon: {lon:.7f}")
            print("--------------------")

            # Add a small delay
            time.sleep(0.05)  # Adjusted for potentially faster updates

    except KeyboardInterrupt:
        print("\nProgram interrupted by user. Exiting...")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        print("Visual Odometry Stopped")

if __name__ == "__main__":
    main()
