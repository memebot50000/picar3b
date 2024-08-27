import cv2
import numpy as np
import time
import subprocess
import io
from PIL import Image
from pymavlink import mavutil

# Initialize MAVLink connection
master = mavutil.mavlink_connection('udpout:localhost:14550')

# Function to capture a frame using rpicam-still
def capture_frame():
    result = subprocess.run(['rpicam-still', '-n', '-o', '-', '-t', '1', '--width', '640', '--height', '480'], capture_output=True)
    image = Image.open(io.BytesIO(result.stdout))
    return cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

# Function to send position to QGroundControl
def send_position(lat, lon, alt, vx, vy, vz, heading):
    master.mav.global_position_int_send(
        int(time.time() * 1000),  # time_boot_ms
        int(lat * 1e7),  # lat
        int(lon * 1e7),  # lon
        int(alt * 1000),  # alt
        int(vx * 100),   # vx
        int(vy * 100),   # vy
        int(vz * 100),   # vz
        int(heading * 100),  # hdg
        0  # relative_alt
    )

def main():
    # Initialize variables for odometry
    prev_frame = None
    x, y = 0, 0  # Starting position
    heading = 0

    # Starting GPS position (36 Cummings Rd, Newton, MA)
    lat, lon = 42.3300, -71.2089

    print("Visual Odometry and MAVLink Communication Started")
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

            # Send position to QGroundControl
            send_position(lat, lon, 0, fx, fy, 0, heading)

            # Update previous frame
            prev_frame = gray

            # Print current position (for debugging)
            print(f"Position: ({x:.2f}, {y:.2f}), Heading: {heading:.2f}")

            # Add a small delay
            time.sleep(0.1)

    except KeyboardInterrupt:
        print("\nProgram interrupted by user. Exiting...")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        print("Visual Odometry and MAVLink Communication Stopped")

if __name__ == "__main__":
    main()
