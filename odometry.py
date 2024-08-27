import cv2
import numpy as np
import time
import subprocess
import io
from PIL import Image
import math

def capture_frame():
    result = subprocess.run(['rpicam-still', '-n', '-o', '-', '-t', '1', '--width', '640', '--height', '480'], capture_output=True)
    image = Image.open(io.BytesIO(result.stdout))
    return cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

class LowPassFilter:
    def __init__(self, tap_coefs):
        self.tap_coefs = tap_coefs
        self.len_coefs = len(tap_coefs)
        self.sample_buffer = [0] * self.len_coefs

    def filter(self, data):
        self.sample_buffer.append(data)
        if len(self.sample_buffer) > self.len_coefs:
            self.sample_buffer.pop(0)
        return sum(c * s for c, s in zip(self.tap_coefs, self.sample_buffer))

class RCCarOpticalFlow:
    def __init__(self):
        self.scalar_x = 1.0
        self.scalar_y = 1.0
        self.rate = 20.0
        self.velocity_x = 0
        self.velocity_y = 0
        self.position_x = 0
        self.position_y = 0
        self.prev_flow_process_time = 0
        self.altitude = 0.0762  # 3 inches in meters
        self.tap_coefs = [0.05, 0.2, 0.5, 0.2, 0.05]
        self.low_pass_filter_x = LowPassFilter(self.tap_coefs)
        self.low_pass_filter_y = LowPassFilter(self.tap_coefs)
        self.low_pass_filter_corrected_x = LowPassFilter(self.tap_coefs)
        self.low_pass_filter_corrected_y = LowPassFilter(self.tap_coefs)

        # Camera calibration data (replace with actual values from manufacturer)
        self.camera_matrix = np.array([[462.0, 0, 320.5],
                                       [0, 462.0, 240.5],
                                       [0, 0, 1]])
        self.dist_coeffs = np.array([0.0, 0.0, 0.0, 0.0, 0.0])

    def reset_pose(self):
        self.position_x = 0
        self.position_y = 0
        self.velocity_x = 0
        self.velocity_y = 0

    def undistort_image(self, image):
        h, w = image.shape[:2]
        newcameramtx, roi = cv2.getOptimalNewCameraMatrix(self.camera_matrix, self.dist_coeffs, (w,h), 1, (w,h))
        return cv2.undistort(image, self.camera_matrix, self.dist_coeffs, None, newcameramtx)

    def process_flow(self):
        if (time.time() - self.prev_flow_process_time) >= (1.0 / self.rate):
            self.prev_flow_process_time = time.time()

            image = capture_frame()
            undistorted = self.undistort_image(image)
            rotated = cv2.rotate(undistorted, cv2.ROTATE_180)
            gray = cv2.cvtColor(rotated, cv2.COLOR_BGR2GRAY)

            if not hasattr(self, 'prev_gray'):
                self.prev_gray = gray
                return

            flow = cv2.calcOpticalFlowFarneback(self.prev_gray, gray, None, 0.5, 3, 15, 3, 5, 1.2, 0)
            self.prev_gray = gray

            x_shift, y_shift = flow.mean(axis=(0, 1))

            x_shift = self.rate * self.altitude * math.atan2(self.scalar_x * x_shift, 500)
            y_shift = self.rate * self.altitude * math.atan2(self.scalar_y * y_shift, 500)

            motion_x = self.low_pass_filter_x.filter(x_shift)
            motion_y = self.low_pass_filter_y.filter(y_shift)

            self.velocity_x = self.low_pass_filter_corrected_x.filter(motion_x)
            self.velocity_y = self.low_pass_filter_corrected_y.filter(motion_y)

            self.update_pose()

    def update_pose(self):
        self.position_x += self.velocity_x * (1.0 / self.rate)
        self.position_y += self.velocity_y * (1.0 / self.rate)

        print(f"Position: ({self.position_x:.4f}, {self.position_y:.4f})")
        print(f"Velocity: ({self.velocity_x:.4f}, {self.velocity_y:.4f})")
        print("--------------------")

    def run(self):
        print("RC Car Optical Flow Started")
        print("Press Ctrl+C to stop")

        try:
            while True:
                self.process_flow()
                time.sleep(1.0 / self.rate)
        except KeyboardInterrupt:
            print("\nProgram interrupted by user. Exiting...")
        except Exception as e:
            print(f"An error occurred: {e}")
        finally:
            print("RC Car Optical Flow Stopped")

if __name__ == "__main__":
    rc_car_flow = RCCarOpticalFlow()
    rc_car_flow.run()
