from gpiozero import Motor
import time

# Set up the motors
drive_motor = Motor(forward=17, backward=27, enable=12)
steer_motor = Motor(forward=22, backward=23, enable=13)

def stop():
    drive_motor.stop()
    steer_motor.stop()

def forward(t):
    '''drives car forward for t seconds'''
    drive_motor.backward()
    time.sleep(t)
    drive_motor.stop()

def backward(t):
    '''drives car backward for t seconds'''
    drive_motor.forward()
    time.sleep(t)
    drive_motor.stop()

def left(d, t):
    '''turns left going d direction for t seconds. d must be "w" or "s"'''
    if d == "w":
        steer_motor.forward()
        forward(t)
        steer_motor.stop()
    elif d == "s":
        steer_motor.forward()
        backward(t)
        steer_motor.stop()
    else:
        stop()

def right(d, t):
    '''turns right going d direction for t seconds. d must be "w" or "s"'''
    if d == "w":
        steer_motor.backward()
        forward(t)
        steer_motor.stop()
    elif d == "s":
        steer_motor.backward()
        backward(t)
        steer_motor.stop()
    else:
        stop()

def test():
    forward(0.5)
    backward(0.5)
    steer_motor.forward()
    time.sleep(0.5)
    steer_motor.stop()
    steer_motor.backward()
    time.sleep(0.5)
    steer_motor.stop()
    print("test completed")

print("RC Car Control Ready. Enter W,A,S,D to control. Enter corresponding times after commands. Enter Q to quit. Enter T to test. Remember to put spaces between commands/times or the code will break.")

while True:
    kcmds = input("Enter command(s): ").lower()
    tcmds = input("Enter time(s): ")
    klst = kcmds.split()
    tlst = tcmds.split()
    tlst = [float(t) for t in tlst]  # Convert times to float
    
    try:
        for i in range(len(klst)):
            if klst[i] == 'w':
                forward(tlst[i])
            elif klst[i] == 's':
                backward(tlst[i])
            elif klst[i] == 'a':
                if i > 0 and klst[i-1] == "w":
                    left("w", tlst[i])
                elif i > 0 and klst[i-1] == "s":
                    left("s", tlst[i])
                else:
                    stop()
            elif klst[i] == 'd':
                if i > 0 and klst[i-1] == "w":
                    right("w", tlst[i])
                elif i > 0 and klst[i-1] == "s":
                    right("s", tlst[i])
                else:
                    stop()
            elif klst[i] == "t":
                test()
            elif klst[i] == 'q':
                stop()
                print("RC Car Control stopped.")
                exit()
            else:
                stop()
    except IndexError:
        print("Error: Number of commands and times do not match.")
    except ValueError:
        print("Error: Invalid time input. Please enter numeric values for times.")
    except Exception as e:
        print(f"An error occurred: {str(e)}")
    
    time.sleep(0.1)  # Short delay to prevent overwhelming the system
