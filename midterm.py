# Bloom - a flower that opens when you flash a light on it
# A flash of light on the photocell triggers the flower: the servo pulls the string
# down, which slides the collar down and opens the flower all the way. It stays open
# for HOLD_TIME seconds and then closes. It does not matter if the light is taken away
# straight away or kept on, any flash brighter than FLASH_RISE does the whole thing.
# A new flash while the flower is open keeps it open longer, and a new flash while it
# is closing makes it open again.
# A NeoPixel strip shows how open the flower is: it fills up pixel by pixel as the
# flower opens and fades out as it closes.

print("bloom")

import time
import board
import digitalio
import neopixel
import pwmio
from adafruit_motor import servo
from analogio import AnalogIn

SERVO_PIN = board.EXTERNAL_SERVO
ASSEMBLY_MODE = False

# Servo settings. 
CLOSED_ANGLE = 20  # flower closed
OPEN_ANGLE = 160  # flower open
OPEN_SPEED = 100  # degrees per second while opening. 
CLOSE_SPEED = 50  # degrees per second while closing
HOLD_TIME = 4.0  # seconds to stay fully open

# Light
FLASH_RISE = 3000  
REARM_BELOW = 1500  

BASELINE_UP_TIME = 20.0  # room getting brighter
BASELINE_DOWN_TIME = 120.0  # room getting darker
BASELINE_LIT_TIME = 60.0 

# NeoPixel strip
STRIP_PIN = board.D5  
NUM_PIXELS = 7
STRIP_RGBW = False  
STRIP_REVERSE = False  
STRIP_COLOR = (255, 140, 40)  
STRIP_DIM = 0.02  
STRIP_BRIGHT = 0.5  

SELF_TEST = False  


# EXTERNAL_POWER enabled
enable = digitalio.DigitalInOut(board.EXTERNAL_POWER)
enable.direction = digitalio.Direction.OUTPUT
enable.value = True
pwm = pwmio.PWMOut(SERVO_PIN, duty_cycle=2 ** 15, frequency=50)
flower = servo.Servo(pwm)

photocell = AnalogIn(board.A1)

# NeoPixel strip
strip = neopixel.NeoPixel(STRIP_PIN, NUM_PIXELS, brightness=1.0,
                          auto_write=False,
                          pixel_order=neopixel.GRBW if STRIP_RGBW else neopixel.GRB)


def show_strip(openness):
    for i in range(NUM_PIXELS):
        fill = max(0.0, min(1.0, openness * NUM_PIXELS - i))
        level = STRIP_DIM + (STRIP_BRIGHT - STRIP_DIM) * fill * fill
        color = tuple(int(c * level) for c in STRIP_COLOR)
        if STRIP_RGBW:
            color += (0,)
        strip[NUM_PIXELS - 1 - i if STRIP_REVERSE else i] = color
    strip.show()


def read_light():
    """Average a few readings, so noise doesn't move the flower."""
    total = 0
    for _ in range(8):
        total += photocell.value
    return total / 8

time.sleep(1)

angle = CLOSED_ANGLE
flower.angle = angle
show_strip(0.0)

if ASSEMBLY_MODE:
    print("assembly mode: holding the closed angle", CLOSED_ANGLE)
    while True:
        time.sleep(1)

if SELF_TEST:
    print("self test: open")
    flower.angle = OPEN_ANGLE
    show_strip(1.0)
    time.sleep(2)
    print("self test: close")
    flower.angle = CLOSED_ANGLE
    show_strip(0.0)
    time.sleep(2)

#flower states
CLOSED = "closed"
OPENING = "opening"
HOLDING = "holding"
CLOSING = "closing"
state = CLOSED
hold_start = 0
armed = True 

# Room's light as the baseline.
baseline = read_light()
last = time.monotonic()
last_print = last

while True:
    now = time.monotonic()
    dt = now - last
    last = now

    light = read_light()
    rise = light - baseline

    if rise < REARM_BELOW:
        armed = True
    if armed and rise > FLASH_RISE:
        armed = False
        if state == HOLDING:
            hold_start = now  
        elif state in (CLOSED, CLOSING):
            state = OPENING
            print("flash!")

    
    if rise > FLASH_RISE:
        follow_time = BASELINE_LIT_TIME
    elif rise < 0:
        follow_time = BASELINE_DOWN_TIME
    else:
        follow_time = BASELINE_UP_TIME
    baseline += rise * dt / follow_time

  
    if state == OPENING:
        target, speed = OPEN_ANGLE, OPEN_SPEED
        if angle == OPEN_ANGLE:
            state = HOLDING
            hold_start = now
    elif state == HOLDING:
        target, speed = OPEN_ANGLE, OPEN_SPEED
        if now - hold_start >= HOLD_TIME:
            state = CLOSING
    elif state == CLOSING:
        target, speed = CLOSED_ANGLE, CLOSE_SPEED
        if angle == CLOSED_ANGLE:
            state = CLOSED
    else:
        target, speed = CLOSED_ANGLE, CLOSE_SPEED

    if speed == 0:
        angle = target
    else:
        step = speed * dt
        if abs(target - angle) <= step:
            angle = target
        elif target > angle:
            angle += step
        else:
            angle -= step
    flower.angle = angle

    openness = (angle - CLOSED_ANGLE) / (OPEN_ANGLE - CLOSED_ANGLE)
    show_strip(max(0.0, min(1.0, openness)))

    if now - last_print > 0.2:
        last_print = now
        print((int(light), int(baseline), int(rise), state, int(angle)))

    time.sleep(0.02)
