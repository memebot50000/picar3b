import cv2
import numpy as np
import time
import subprocess
import io
from PIL import Image
from collections import deque

def capture_frame():
    result = subprocess.run(['rpicam-still', '-n', '-o', '-', '-t', '1', '--width', '640', '--height', '480'], capture_output=True)
    image = Image.open(io.BytesIO(result.stdout))
    return cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

def calculate_average_flow(flow):
    h, w = flow.shape[:2]
    fx, fy = flow[h//4:3*h//4, w//4:3*w//4].mean(axis=(0, 1))
    return fx, fy

# Camera calibration data (replace with actual values from manufacturer)
camera_matrix = np.array([[462.0, 0, 320.5],
                          [0, 462.0, 240.5],
                          [0, 0, 1]])
dist_coeffs = np.array([0.0, 0.0, 0.0, 0.0, 0.0])

def undistort_image(image):
    h, w = image.shape[:2]
    newcameramtx, roi = cv2.getOptimalNewCameraMatrix(camera_matrix, dist_coeffs, (w,h), 1, (w,h))
    undistorted = cv2.undistort(image, camera_matrix, dist_coeffs, None, newcameramtx)
    return undistorted

def main():
    prev_frame = None
    x, y = 0, 0
    heading = 0

    lat, lon = 42.3300, -71.2089

    # Adjusted parameters
    scale = 2.0
    smoothing_window = 3
    x_smooth = deque([0] * smoothing_window, maxlen=smoothing_window)
    y_smooth = deque([0] * smoothing_window, maxlen=smoothing_window)

    gps_factor = 1e-5

    print("Visual Odometry Started")
    print("Press Ctrl+C to stop")

    try:
        while True:
            image = capture_frame()
            
            # Undistort the image using calibration data
            undistorted = undistort_image(image)
            
            # Rotate the image 180 degrees to account for camera orientation
            rotated = cv2.rotate(undistorted, cv2.ROTATE_180)

            if prev_frame is None:
                prev_frame = cv2.cvtColor(rotated, cv2.COLOR_BGR2GRAY)
                continue

            gray = cv2.cvtColor(rotated, cv2.COLOR_BGR2GRAY)

            flow = cv2.calcOpticalFlowFarneback(prev_frame, gray, None, 0.5, 3, 15, 3, 7, 1.5, 0)

            fx, fy = calculate_average_flow(flow)
            
            # Swap x and y to account for camera orientation
            x += fy * scale
            y -= fx * scale
            x_smooth.append(x)
            y_smooth.append(y)
            x_smoothed = sum(x_smooth) / smoothing_window
            y_smoothed = sum(y_smooth) / smoothing_window

            heading = np.arctan2(-fx, fy)  # Adjusted for camera orientation

            lat += y_smoothed * gps_factor
            lon += x_smoothed * gps_factor

            prev_frame = gray

            print(f"Raw Position: ({x:.4f}, {y:.4f})")
            print(f"Smoothed Position: ({x_smoothed:.4f}, {y_smoothed:.4f})")
            print(f"Heading: {heading:.2f}")
            print(f"GPS: Lat: {lat:.7f}, Lon: {lon:.7f}")
            print("--------------------")

            time.sleep(0.1)

    except KeyboardInterrupt:
        print("\nProgram interrupted by user. Exiting...")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        print("Visual Odometry Stopped")

if __name__ == "__main__":
    main()
