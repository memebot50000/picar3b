from gpiozero import Motor
import evdev
import time

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
        # Normalize throttle and steering to 0-1 range
        throttle = normalize(throttle_value, joystick.absinfo(evdev.ecodes.ABS_Y).min, joystick.absinfo(evdev.ecodes.ABS_Y).max)
        steering = normalize(steering_value, joystick.absinfo(evdev.ecodes.ABS_X).min, joystick.absinfo(evdev.ecodes.ABS_X).max)
        
        # Convert to -1 to 1 range
        throttle = (throttle - 0.5) * 2
        steering = (steering - 0.5) * 2

        print(f"Throttle: {throttle:.2f}, Steering: {steering:.2f}")  # Debug print

        try:
            # Drive motor control
            if abs(throttle) > 0.1:  # Add a small deadzone
                if throttle > 0:
                    drive_motor.forward(throttle)
                else:
                    drive_motor.backward(-throttle)
            else:
                drive_motor.stop()

            # Steering motor control
            if abs(steering) > 0.1:  # Add a small deadzone
                if steering > 0:
                    steer_motor.backward()
                else:
                    steer_motor.forward()
            else:
                steer_motor.stop()

        except ValueError as e:
            print(f"Error controlling motors: {e}")

    print("RC Car Control Ready. Use the Spektrum controller to control the car. Press Ctrl+C to quit.")

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
        print("RC Car Control stopped.")

if __name__ == "__main__":
    rc_car_control()
