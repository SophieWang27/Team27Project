# Exercise selector and breadboard button

This guide explains how to change exercise modes in the software and how to add an optional physical button. The camera prototype can be used without any extra hardware.

## Switch exercises with the keyboard

Start the tracker, click the camera preview so it is active, then press:

| Key | Mode |
| --- | --- |
| `1` | Deep squat |
| `2` | Plank hold |
| `3` | Bicep curl |
| `4` | Arm rainbow |
| `5` | Farmer's carry |
| `6` | Good morning |
| `N` | Move to the next mode |
| `Q` | Quit |

Modes cycle in the order above. The camera preview shows the current mode, status, feedback, and that mode's completed rep or hold count. A mode keeps its count while the program is running. Selecting a mode again clears an in-progress rep/hold and restarts its setup; the deep squat begins its 30-frame upright calibration again. Counts start over when the program closes.

## Add a physical next-exercise button

The optional physical selector is a momentary push button (a small tactile breadboard button), not an on/off latching switch. Each press advances to the next mode. You can keep using the keyboard even after adding it.

### Parts

- Arduino Uno R4 Minima already connected to the display
- Small four-leg tactile push button
- Breadboard and two jumper wires
- USB data cable between the Arduino and the computer running Python

### Wiring

1. Unplug USB power from the Arduino while wiring.
2. Place the push button across the breadboard's center gap. The two legs on each side are internally connected; the button connects the two sides when pressed.
3. Connect one side of the button to **D2** on the Uno R4.
4. Connect the opposite side of the button to an Arduino **GND** pin.
5. Do not connect this button to 5 V. The Arduino firmware enables its built-in pull-up resistor, so no external resistor is needed.

```text
Arduino D2 ----[ momentary button ]---- Arduino GND
```

### Upload and use the updated firmware

1. In Arduino IDE, open `arduino/uno_r4_display/uno_r4_display.ino` from this project.
2. Select **Arduino Uno R4 Minima** and the correct serial port.
3. Upload the sketch. It now reads the display updates from Python and sends `MODE_NEXT` back to Python when the D2 button is pressed.
4. Connect the Arduino by USB to the same computer that runs the Python tracker. If the Uno is connected to the Raspberry Pi instead, Python must run on the Pi and use that Uno's serial port.
5. Set `SERIAL_PORT` in the project's `.env` file to the Arduino's port. On macOS it often starts with `/dev/cu.usbmodem`; on Linux it often starts with `/dev/ttyACM`.
6. Close Arduino Serial Monitor, because it can occupy the port. Start the Python tracker again. The display should show the active mode; press the button to cycle.

Python sends display text using this line format:

```text
mode|completed_count|status|feedback
```

The button sends this line in the reverse direction:

```text
MODE_NEXT
```

## If the button does not switch modes

- Check that the button straddles the breadboard center gap; same-side legs are already connected.
- Confirm one side reaches D2 and the other reaches GND, with no wire to 5 V.
- Confirm the updated sketch was uploaded to the Uno R4.
- Confirm `.env` names the Arduino's serial port and that Arduino Serial Monitor is closed.
- Check the VS Code terminal for a message that the Arduino display connected. If it says output is disabled, set `SERIAL_PORT` and restart Python.
- Use keys `1` through `6` in the preview as a fallback.

The rep rules are still a prototype. For which checks come directly from the research notes and which are provisional, see the README section **What the prototype measures** and `data/research_rules.md`.
