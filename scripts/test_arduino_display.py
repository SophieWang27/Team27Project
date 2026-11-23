"""Bench-test the Arduino OLED/LEDs/button with no camera or pose model.

Usage:  python scripts/test_arduino_display.py /dev/cu.usbmodemXXXX
Sends fake rep counts every second (GOOD = green LED, DEPTH = red LED) and
prints MODE_NEXT whenever the D2 button is pressed. Ctrl+C to stop.
"""
import sys
import time

import serial  # pyserial

port = sys.argv[1] if len(sys.argv) > 1 else None
if not port:
    sys.exit("Give the Arduino port, e.g. python scripts/test_arduino_display.py /dev/cu.usbmodem1101")

ser = serial.Serial(port, 115200, timeout=0.1)
time.sleep(2)  # the Uno R4 may restart when the port opens
demo = [
    ("deep_squat", "GOOD", "Good repetition"),
    ("deep_squat", "DEPTH", "Squat deeper"),
    ("bicep_curl", "GOOD", "Curl completed"),
    ("plank", "HOLDING", "Hold steady: 3/10 sec"),
]
reps = 0
try:
    for step in range(1000):
        mode, status, text = demo[step % len(demo)]
        if status == "GOOD":
            reps += 1
        ser.write(f"{mode}|{reps}|{status}|{text}\n".encode("ascii"))
        print(f"sent: {mode} reps={reps} {status}")
        end = time.time() + 1
        while time.time() < end:
            if ser.readline().strip() == b"MODE_NEXT":
                print("button press received (MODE_NEXT)")
except KeyboardInterrupt:
    pass
finally:
    ser.close()
