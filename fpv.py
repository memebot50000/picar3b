from gpiozero import Motor
import evdev
import time
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
import cv2
import io
import subprocess

# Function to get the Raspberry Pi's IP address
def get_ip_address():
    cmd = "hostname -I"
    return subprocess.check_output(cmd, shell=True).decode('utf-8').strip().split()[0]

# RC Car Control Setup
SPEKTRUM_VENDOR_ID = 0x0483
SPEKTRUM_PRODUCT_ID = 0x572b

def find_spektrum_device():
    devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
    for device in devices:
        if device.info.vendor == SPEKTRUM_VENDOR_ID and device.info.product == SPEKTRUM_PRODUCT_ID:
            return device
    return None

def normalize(value, min_val, max_val):
    return (value - min_val) / (max_val - min_val)

# Camera Setup
camera = cv2.VideoCapture(0)  # Use 0 for the first USB camera
camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

# Streaming Setup
class StreamingHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(301)
            self.send_header('Location', '/index.html')
            self.end_headers()
        elif self.path == '/index.html':
            content = """
            <html>
            <head>
                <title>RC Car Stream</title>
            </head>
            <body>
                <h1>RC Car Video Stream</h1>
                <img src="stream.mjpg" width="640" height="480" />
            </body>
            </html>
            """
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.send_header('Content-Length', len(content))
            self.end_headers()
            self.wfile.write(content.encode('utf-8'))
        elif self.path == '/stream.mjpg':
            self.send_response(200)
            self.send_header('Age', 0)
            self.send_header('Cache-Control', 'no-cache, private')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Content-Type', 'multipart/x-mixed-replace; boundary=FRAME')
            self.end_headers()
            try:
                while True:
                    ret, frame = camera.read()
                    if not ret:
                        continue
                    _, jpeg = cv2.imencode('.jpg', frame)
                    self.wfile.write(b'--FRAME\r\n')
                    self.send_header('Content-Type', 'image/jpeg')
                    self.send_header('Content-Length', len(jpeg))
                    self.end_headers()
                    self.wfile.write(jpeg.tobytes())
                    self.wfile.write(b'\r\n')
            except Exception as e:
                print(f"Removed streaming client {self.client_address}: {str(e)}")
        else:
            self.send_error(404)
            self.end_headers()

class StreamingServer(HTTPServer):
    allow_reuse_address = True
    daemon_threads = True

# Main Control Function
def rc_car_control():
    drive_motor = Motor(forward=17, backward=27, enable=12)
    steer_motor = Motor(forward=22, backward=23, enable=13)

    joystick = find_spektrum_device()
    if not joystick:
        print("Spektrum receiver not found. Please make sure it's connected.")
        return

    print(f"Using device: {joystick.name}")

    def stop():
        drive_motor.stop()
        steer_motor.stop()

    def control_motors(throttle_value, steering_value):
        throttle = normalize(throttle_value, joystick.absinfo(evdev.ecodes.ABS_Y).min, joystick.absinfo(evdev.ecodes.ABS_Y).max)
        steering = normalize(steering_value, joystick.absinfo(evdev.ecodes.ABS_X).min, joystick.absinfo(evdev.ecodes.ABS_X).max)
        
        throttle = (throttle - 0.5) * 2
        steering = (steering - 0.5) * 2

        print(f"Throttle: {throttle:.2f}, Steering: {steering:.2f}")

        try:
            if abs(throttle) > 0.1:
                if throttle > 0:
                    drive_motor.forward(throttle)
                else:
                    drive_motor.backward(-throttle)
            else:
                drive_motor.stop()

            if abs(steering) > 0.1:
                if steering > 0:
                    steer_motor.backward()
                else:
                    steer_motor.forward()
            else:
                steer_motor.stop()

        except ValueError as e:
            print(f"Error controlling motors: {e}")

    print("RC Car Control Ready. Use the Spektrum controller to control the car. Press Ctrl+C to quit.")

    # Get the Raspberry Pi's IP address
    ip_address = get_ip_address()
    
    # Start the HTTP server
    port = 8000
    address = (ip_address, port)
    server = StreamingServer(address, StreamingHandler)
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.daemon = True
    server_thread.start()
    print(f"Server started at http://{ip_address}:{port}")

    throttle_value = 0
    steering_value = 0

    try:
        for event in joystick.read_loop():
            if event.type == evdev.ecodes.EV_ABS:
                if event.code == evdev.ecodes.ABS_Y:  # Throttle
                    throttle_value = event.value
                elif event.code == evdev.ecodes.ABS_X:  # Steering
                    steering_value = event.value
                control_motors(throttle_value, steering_value)

    except KeyboardInterrupt:
        print("\nProgram interrupted by user. Exiting...")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        stop()
        camera.release()
        server.shutdown()
        print("RC Car Control stopped.")

if __name__ == "__main__":
    rc_car_control()
