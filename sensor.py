"""
LIGHTHOUSE
-----------------
OVERVIEW
  Photocell     -> time of day. Bright room = lighthouse sleeps (dim breathing
                   glow, servo parked, silent). Dark room = it wakes up gradually.
  Potentiometer -> fog. More fog = slower sweep, shorter and bluer beam,
                   more frequent and lower foghorn.
  Servo         -> the rotating lamp. NeoPixel ring -> the beam. Speaker -> foghorn.

WIRING 
  Potentiometer: outer legs to 3V3 and GND, middle leg to A0
  Photocell:     3V3 -> photocell -> A1 -> 10k resistor -> GND
  NeoPixel ring: DIN -> A2, PWR -> 5V, GND -> GND
  Speaker:       A3 -> 300 ohm resistor -> speaker (+); speaker (-) -> GND
  Servo:         signal -> D10, red -> 5V, brown/black -> GND
"""

import time
import math
import board
import analogio
import pwmio
import neopixel

NUM_PIXELS = 12   

pot = analogio.AnalogIn(board.A0)
photocell = analogio.AnalogIn(board.A1)

ring = neopixel.NeoPixel(board.A2, NUM_PIXELS, brightness=0.4, auto_write=False)
speaker = pwmio.PWMOut(board.A3, frequency=140, duty_cycle=0, variable_frequency=True)
servo = pwmio.PWMOut(board.D10, frequency=50, duty_cycle=0)

LIGHT_MIN = 15000   
LIGHT_MAX = 60000   

CLEAR_BEAM = (255, 190, 70)   # warm light in clear weather
FOG_BEAM = (110, 150, 220)    # cold light in thick fog
WINDOW_GLOW = (255, 120, 20)  # sleepy window glow


def map_range(x, in_min, in_max, out_min, out_max):
    x = max(in_min, min(in_max, x))
    return out_min + (x - in_min) * (out_max - out_min) / (in_max - in_min)

def read_avg(sensor, n=8):
    total = 0
    for _ in range(n):
        total += sensor.value
    return total / n

def set_servo_angle(angle):
    pulse_ms = map_range(angle, 0, 180, 0.5, 2.5)
    servo.duty_cycle = int(pulse_ms / 20 * 65535)

def mix(a, b, t):
    return tuple(a[i] + (b[i] - a[i]) * t for i in range(3))


wake = 0.0            # 0 = fast asleep, 1 = fully awake
pos = 0.5          
direction = 1
last = time.monotonic()
next_horn = last
horn_until = 0
last_print = 0

while True:
    now = time.monotonic()
    dt = now - last
    last = now

    light = read_avg(photocell)
    fog = map_range(read_avg(pot), 0, 65535, 0.0, 1.0)
    night = map_range(light, LIGHT_MIN, LIGHT_MAX, 1.0, 0.0)

    # gradual waking/sleeping 
    wake += (night - wake) * min(1.0, dt * 1.5)

    # Beam sweep
    speed = 1.8 - 1.2 * fog
    pos += direction * speed * wake * dt
    if pos >= 1.0:
        pos, direction = 1.0, -1
    elif pos <= 0.0:
        pos, direction = 0.0, 1

    set_servo_angle(90 + (pos - 0.5) * 180 * wake)

    # LIGHT
    beam_color = mix(CLEAR_BEAM, FOG_BEAM, fog)
    tail = 3.0 - 1.8 * fog
    center = pos * (NUM_PIXELS - 1)
    breathe = 0.5 + 0.5 * math.sin(now * 1.5)
    glow = (1.0 - wake) * (0.05 + 0.10 * breathe)

    for i in range(NUM_PIXELS):
        behind = (center - i) * direction      
        if behind >= 0:
            beam = 1.0 - behind / tail
        else:
            beam = 1.0 - (-behind) / 0.8
        beam = max(0.0, beam) * wake
        ring[i] = tuple(
            min(255, int(beam_color[c] * beam + WINDOW_GLOW[c] * glow))
            for c in range(3)
        )
    ring.show()

    # SOUND
    if wake > 0.6 and now >= next_horn:
        speaker.frequency = int(map_range(fog, 0, 1, 180, 110))
        horn_until = now + 0.8
        next_horn = now + 9.0 - 7.0 * fog
    if now < horn_until and wake > 0.3:
        speaker.duty_cycle = 2**14
    else:
        speaker.duty_cycle = 0

    if now - last_print > 0.5:
        print((int(light), round(fog, 2), round(wake, 2)))
        last_print = now

    time.sleep(0.02)
