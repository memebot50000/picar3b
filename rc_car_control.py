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

    print("RC Car Control Ready. Use the Spektrum controller to control the car. Press Ctrl+C to quit.")

    throttle = 127
    steering = 127

    try:
        for event in joystick.read_loop():
            if event.type == evdev.ecodes.EV_ABS:
                if event.code == evdev.ecodes.ABS_Y:  # Throttle
                    throttle = event.value
                elif event.code == evdev.ecodes.ABS_X:  # Steering
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
