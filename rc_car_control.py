from gpiozero import Motor
import pygame
import time

def rc_car_control():
    drive_motor = Motor(forward=17, backward=27, enable=12)
    steer_motor = Motor(forward=22, backward=23, enable=13)

    pygame.init()
    pygame.joystick.init()

    if pygame.joystick.get_count() == 0:
        print("No joystick detected. Please connect the WS2000 dongle.")
        return

    joystick = pygame.joystick.Joystick(0)
    joystick.init()

    def stop():
        drive_motor.stop()
        steer_motor.stop()

    def control_motors(throttle, steering):
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

    print("RC Car Control Ready. Use the WS2000 dongle to control the car. Press Q to quit.")

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        throttle = joystick.get_axis(1)  # Assuming axis 1 is throttle
        steering = joystick.get_axis(0)  # Assuming axis 0 is steering

        # Invert and scale the inputs if necessary
        throttle = -throttle  # Invert if up is negative
        
        # Apply a small deadzone to prevent unwanted movement
        if abs(throttle) < 0.1:
            throttle = 0
        if abs(steering) < 0.1:
            steering = 0

        control_motors(throttle, steering)

        # Check for quit button (assuming it's the first button)
        if joystick.get_button(0):
            running = False

        time.sleep(0.01)  # Short delay to prevent overwhelming the system

    stop()
    pygame.quit()
    print("RC Car Control stopped.")

if __name__ == "__main__":
    rc_car_control()
