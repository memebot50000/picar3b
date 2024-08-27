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

class SimpleKalmanFilter:
    def __init__(self, process_variance, measurement_variance, initial_value=0):
        self.process_variance = process_variance
        self.measurement_variance = measurement_variance
        self.estimate = initial_value
        self.estimate_error = 1

    def update(self, measurement):
        prediction = self.estimate
        prediction_error = self.estimate_error + self.process_variance

        kalman_gain = prediction_error / (prediction_error + self.measurement_variance)
        self.estimate = prediction + kalman_gain * (measurement - prediction)
        self.estimate_error = (1 - kalman_gain) * prediction_error

        return self.estimate

def main():
    prev_frame = None
    x, y = 0, 0
    heading = 0

    lat, lon = 42.3300, -71.2089

    # Adjusted parameters
    scale = 0.5  # Reduced scale factor
    motion_threshold = 0.001  # Threshold to ignore small movements

    # Kalman filters for x and y
    kf_x = SimpleKalmanFilter(process_variance=1e-5, measurement_variance=0.1**2)
    kf_y = SimpleKalmanFilter(process_variance=1e-5, measurement_variance=0.1**2)

    print("Visual Odometry Started")
    print("Press Ctrl+C to stop")

    try:
        while True:
            image = capture_frame()
            
            undistorted = undistort_image(image)
            rotated = cv2.rotate(undistorted, cv2.ROTATE_180)

            if prev_frame is None:
                prev_frame = cv2.cvtColor(rotated, cv2.COLOR_BGR2GRAY)
                continue

            gray = cv2.cvtColor(rotated, cv2.COLOR_BGR2GRAY)

            # Adjusted optical flow parameters
            flow = cv2.calcOpticalFlowFarneback(prev_frame, gray, None, 0.5, 5, 15, 3, 5, 1.1, 0)

            fx, fy = calculate_average_flow(flow)
            
            # Apply motion threshold
            if abs(fx) > motion_threshold or abs(fy) > motion_threshold:
                x += fy * scale
                y -= fx * scale
            else:
                fx, fy = 0, 0

            # Apply Kalman filter
            x_filtered = kf_x.update(x)
            y_filtered = kf_y.update(y)

            heading = np.arctan2(-fx, fy) if fx != 0 or fy != 0 else heading

            lat += y_filtered * 1e-7  # Adjusted GPS factor
            lon += x_filtered * 1e-7  # Adjusted GPS factor

            prev_frame = gray

            print(f"Raw Position: ({x:.4f}, {y:.4f})")
            print(f"Filtered Position: ({x_filtered:.4f}, {y_filtered:.4f})")
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
