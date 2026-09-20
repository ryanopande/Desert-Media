import time
import board
from rainbowio import colorwheel
import neopixel


pixel = neopixel.NeoPixel(board.NEOPIXEL, 1)
pixel.brightness = 0.3


def one_day(delay):
    # Night
    for twinkle in range(5):
        pixel[0] = (0, 0, 255)                     # blue night
        time.sleep(0.9)
        pixel[0] = (255, 255, 255)                 # star flash
        time.sleep(0.1)


    for value in range(256):                       # dawn: blue -> purple -> red
        pixel[0] = (value, 0, 255 - value)
        time.sleep(delay)

    for value in range(256):                       # sunrise: red -> orange -> yellow
        pixel[0] = (255, value, 0)
        time.sleep(delay)

    for value in range(256):                       # midday: yellow -> bright white
        pixel[0] = (255, 255, value)
        time.sleep(delay)

    for value in range(256):                       # afternoon: white -> yellow
        pixel[0] = (255, 255, 255 - value)
        time.sleep(delay)

    for value in range(256):                       # sunset: yellow -> orange -> red
        pixel[0] = (255, 255 - value, 0)
        time.sleep(delay)

    for value in range(256):                       # dusk: red -> purple -> blue
        pixel[0] = (255 - value, 0, value)
        time.sleep(delay)



while True:
    one_day(0.016)