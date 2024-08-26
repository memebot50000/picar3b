from gpiozero import Motor
from evdev import InputDevice, categorize, ecodes
import time
import select
import os

def rc_car_control():
    drive_motor = Motor(forward=17, backward=27, enable=12)
    steer_motor = Motor(forward=22, backward=23, enable=13)

    # Find the WS2000 dongle
    devices = []
    for fn in os.listdir("/dev/input"):
        if fn.startswith("event"):
            try:
                device = InputDevice(os.path.join("/dev/input", fn))
                if "Spektrum" in device.name:
                    joystick = device
                    break
                devices.append(device)
            except PermissionError:
                print(f"Permission denied for /dev/input/{fn}. Try running with sudo.")
            except Exception as e:
                print(f"Error opening /dev/input/{fn}: {e}")
    else:
        print("Spektrum WS2000 dongle not found. Please connect it and try again.")
        return

    print(f"Using device: {joystick.name}")

    def stop():
        drive_motor.stop()
        steer_motor.stop()

    def control_motors(throttle, steering):
        throttle = (throttle - 127) / 127.0  # Convert to range -1 to 1
        steering = (steering - 127) / 127.0  # Convert to range -1 to 1

        if throttle > 0:
            drive_motor.forward(abs(throttle))
        elif throttle < 0:
            drive_motor.backward(abs(throttle))
        else:
            drive_motor.stop()

        if steering > 0:
            steer_motor.forward(abs(steering))
        elif steering < 0:
            steer_motor.backward(abs(steering))
        else:
            steer_motor.stop()

    print("RC Car Control Ready. Use the WS2000 dongle to control the car. Press Ctrl+C to quit.")

    throttle = 127
    steering = 127

    try:
        while True:
            r, w, x = select.select([joystick], [], [], 0.01)
            if r:
                for event in joystick.read():
                    if event.type == ecodes.EV_ABS:
                        if event.code == ecodes.ABS_Y:  # Throttle
                            throttle = event.value
                        elif event.code == ecodes.ABS_X:  # Steering
                            steering = event.value

            control_motors(throttle, steering)

    except KeyboardInterrupt:
        print("\nProgram interrupted by user. Exiting...")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        stop()
        print("RC Car Control stopped.")

if __name__ == "__main__":
    rc_car_control()
