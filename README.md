# Team 27 Exercise Tracker

This is our laptop-first prototype for ECE 198 subproblem 2: exercise tracking and measurement. It uses a webcam or an ESP32-CAM stream, estimates one person's pose with Google's pretrained MediaPipe model, and checks deep-squat repetitions against the measurements in our research notes. If an Arduino Uno R4 is connected, the rep count and feedback can also appear on its OLED.

Start with the laptop camera. The ESP32-CAM, Arduino display, and Raspberry Pi are optional steps after that run works.

//

When `.venv` and the model are in the project folder, open **Terminal → New Terminal** in VS Code and run:

```bash
source .venv/bin/activate
python -m src.main --source 0
```

The preview window should show the camera image, detected skeleton, rep count, feedback, and processing speed. Press **Q** in the preview window to stop. You can also press **Control+C** in the VS Code terminal.

For the first 30 visible frames, stand upright and still so the program can set its starting position. Then stay side-on to the camera with your whole body in view. Good lighting helps the pose model find your knees and ankles.

The terminal prints performance every five seconds. It includes processing FPS, average pose-inference time, and camera-frame size. Use this when comparing the laptop with a Raspberry Pi.

If you use a different webcam, replace `0` with its camera number. For a video file, pass the file path instead. The ESP32-CAM URL can also be passed as the source; its setup is below.

## Set up a fresh copy

Install [Visual Studio Code](https://code.visualstudio.com/download), its [Python extension](https://marketplace.visualstudio.com/items?itemName=ms-python.python), and [Python 3.11](https://www.python.org/downloads/release/python-31118/). In VS Code, open the `Team27Project` folder and create the Python environment in the integrated terminal:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

If the folder does not already contain a `.env` file, make one from the example:

```bash
cp .env.example .env
```

Choose the `.venv` Python interpreter in VS Code with **Command Palette → Python: Select Interpreter**.

The pretrained model is a separate download. It is already in this copy under `models/`. If it is missing, run:

```bash
python scripts/download_model.py --variant lite
```

That downloads Google's [Pose Landmarker Lite model](https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/1/pose_landmarker_lite.task). The app uses the model to find body landmarks; the research rules are separate data in `data/research_rules.json`.

On Windows, create the environment with `py -3.11 -m venv .venv` and activate it with `.venv\Scripts\activate`.

## What the prototype measures

The first exercise is the deep squat because our notes provide a depth target and two standing-recovery checks. The program loads these default values from `data/research_rules.json`:

| Check | Value used by the program |
| --- | ---: |
| Minimum squat depth | 29.1% of the calibrated image height |
| Maximum hip/waist return drift | 0.50% |
| Maximum head return drift | 0.169% |

The 29.1% value comes from the 32.1% depth reference in the notes with a 3 percentage-point margin. The other limits combine the reported recovery values with the error margins written in the notes. In this version, image height is estimated from the visible nose-to-ankle distance; the program does not ask for a person's height in centimetres.

Plank, curl, arm-rainbow, farmer's-carry, and good-morning notes are saved in the same research files. They are not active modes yet because the notes leave details such as movement phases, angle conventions, or thresholds unresolved. We should confirm those details with the team before using them to count repetitions.

These measurements are for a class prototype. They have not been validated for clinical or safety decisions.

## Research data and optional dataset

The values above are transcribed from **Team27 Research Page.docx** and are used by the running code. See `data/research_rules.md` for the full list of exercise notes and `data/research_rules.json` for the values the app reads.

The raw [UI-PRMD dataset](https://zenodo.org/records/23104965) is optional. It is not needed to run the camera demo and is not loaded by the app. If the team wants to inspect examples, start with the [segmented movements archive](https://zenodo.org/records/23104965/files/Segmented%20Movements.zip?download=1) and [incorrect segmented movements archive](https://zenodo.org/records/23104965/files/Incorrect%20Segmented%20Movements.zip?download=1). Extract them under `data/ui_prmd/`; that folder is excluded from Git. UI-PRMD uses Vicon/Kinect measurements, so its coordinates are not a direct match for MediaPipe's 2D camera landmarks.

## Use the ESP32-CAM instead of the laptop camera

This firmware is written for the AI Thinker ESP32-CAM. You will need the board, a suitable 5 V supply, and a USB-to-serial adapter to upload the code. Install [Arduino IDE](https://www.arduino.cc/en/software), then follow Espressif's [Arduino-ESP32 installation guide](https://docs.espressif.com/projects/arduino-esp32/en/latest/installing.html). The Boards Manager URL is:

```text
https://espressif.github.io/arduino-esp32/package_esp32_index.json
```

In `camera/esp32_cam_stream/`:

1. Copy `secrets.h.example` to `secrets.h` and enter your 2.4 GHz Wi-Fi name and password.
2. Open `esp32_cam_stream.ino` in Arduino IDE and select **AI Thinker ESP32-CAM**.
3. Connect IO0 to GND, upload, disconnect IO0 from GND, and press Reset.
4. Open Serial Monitor at 115200 baud. Note the camera's IP address.
5. On a device on the same Wi-Fi, open `http://CAMERA-IP/` to check that it is online. The video stream is `http://CAMERA-IP:81/stream`.

To run the tracker from VS Code, change `CAMERA_SOURCE` in `.env` to the stream URL, then run:

```bash
python -m src.main
```

The actual setting should look like `CAMERA_SOURCE=http://192.168.1.123:81/stream`, using the IP printed by your board.

## Connect the Arduino display

The sketch in `arduino/uno_r4_display/` expects an Arduino Uno R4 Minima and a 128×64 SSD1306 I2C OLED. Install the **Arduino UNO R4 Boards** package and the **U8g2** library in Arduino IDE, then open and upload `uno_r4_display.ino`.

| Display part | Uno R4 connection |
| --- | --- |
| OLED SDA / SCL | SDA / SCL pins |
| OLED VCC / GND | Use the supply voltage specified for your OLED module, plus GND |
| Green LED | D8 through a 470 Ω resistor to GND |
| Red LED | D9 through a 470 Ω resistor to GND |

Find the Arduino port in **Tools → Port**. Put it in `.env`, for example `SERIAL_PORT=/dev/cu.usbmodemXXXX`, then restart the Python program. Leave `SERIAL_PORT=` empty to use the camera prototype without the display.

The Python program sends one line when the display changes:

```text
rep_count|status|feedback
```

For example: `2|DEPTH|Squat deeper`.

## Project files

There are 18 source and setup files for this prototype. The downloaded model, `.env`, Python environment, Wi-Fi credentials, and optional dataset stay on each computer and are not committed to GitHub.

```text
Team27Project/
├── README.md                         Setup and run instructions
├── .env.example                      Local camera and serial settings template
├── .gitignore                        Files to keep out of Git
├── requirements.txt                  Python packages
├── src/
│   ├── main.py                       Camera loop, preview, and performance readout
│   ├── pose_estimator.py              MediaPipe model wrapper
│   ├── squat_counter.py               Squat measurements and rep counting
│   ├── serial_display.py              Sends feedback to the Arduino
│   ├── config.py                      Loads settings and research thresholds
│   └── __init__.py
├── data/
│   ├── research_rules.json            Defaults read by the squat counter
│   ├── research_rules.md              Research-note transcription
│   └── README.md                      UI-PRMD dataset notes
├── models/README.md                  Pretrained model download notes
├── scripts/download_model.py          Downloads the MediaPipe model
├── camera/esp32_cam_stream/           ESP32-CAM Wi-Fi streaming firmware
└── arduino/uno_r4_display/             OLED and LED display firmware
```

The existing `src/index.html` file in the VS Code folder belongs to a separate placeholder and is not used by this Python prototype.

## Share the code with your teammate

Commit the source and setup files. Keep `.env`, `camera/esp32_cam_stream/secrets.h`, `.venv/`, `models/*.task`, and `data/ui_prmd/` out of GitHub; `.gitignore` already excludes them. After cloning, your teammate can follow **Set up a fresh copy** and download their own model file.

## Try it on the Raspberry Pi

First measure the laptop version using the performance line in the terminal. To run without the preview window, use:

```bash
python -m src.main --source 0 --headless --stats-interval 5
```

For a camera stream, replace `0` with the ESP32-CAM URL. Record FPS, inference time, frame size, CPU use, and memory use. The Zero 2 W has 512 MB of RAM, so test the actual model and camera settings before relying on it; if the response is too slow, run inference on a more capable Pi and keep the same camera and serial connections.

Google's [Pose Landmarker guide](https://ai.google.dev/edge/mediapipe/solutions/vision/pose_landmarker/python) has the model and API details. Raspberry Pi's [Zero 2 W documentation](https://www.raspberrypi.com/documentation/computers/zero.html) lists the board specifications.
