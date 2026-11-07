# Team 27 Exercise Tracking Prototype

This starter project addresses subproblem 2 by taking one local video stream, estimating one person's pose, checking a deep-squat repetition against configurable 2D rules, and optionally sending the count and feedback to an Arduino Uno R4 Minima. The active squat defaults are transcribed from the Team 27 research page and loaded from `data/research_rules.json`. They are classroom-prototype starting points, not clinically validated thresholds.

## What to create and download

The project contains **18 source and setup files**. You download one pretrained pose-model file. UI-PRMD is a separate, optional research dataset; it is not needed for the live camera demo.

```text
team27-exercise-tracker/
├── .env.example                         # Example settings; copy this to .env
├── .gitignore                           # Keeps credentials, model, data, and venv out of Git
├── README.md                            # Setup and run guide
├── requirements.txt                     # Python libraries
├── arduino/uno_r4_display/uno_r4_display.ino # Arduino OLED and LED display
├── camera/esp32_cam_stream/
│   ├── esp32_cam_stream.ino             # ESP32-CAM Wi-Fi MJPEG stream
│   └── secrets.h.example                # Wi-Fi credential template
├── data/README.md                       # UI-PRMD download and use notes
├── data/research_rules.md               # Human-readable transcription of the team research data
├── data/research_rules.json             # Machine-readable rules; squat app loads these defaults
├── models/README.md                     # Model download notes
├── scripts/download_model.py            # Downloads Google's pretrained pose model
└── src/
    ├── __init__.py
    ├── config.py                        # Reads .env settings
    ├── main.py                          # Connects video, pose, counter, and serial output
    ├── pose_estimator.py                # Runs MediaPipe Pose Landmarker
    ├── serial_display.py                # Sends rep/status/feedback to the Arduino
    └── squat_counter.py                 # Squat measurements and repetition state machine
```

Files you create or download locally, but keep out of Git:

- `models/pose_landmarker_lite.task`: downloaded pretrained model; do not commit it.
- `.env`: your local camera URL and serial port; do not commit it.
- `camera/esp32_cam_stream/secrets.h`: your Wi-Fi name and password; do not commit it.
- `data/ui_prmd/`: optional extracted research dataset; do not commit it.
- `.venv/`: your local Python environment; do not commit it.

## Downloads

### 1. Install the laptop tools

1. Download and install [Visual Studio Code](https://code.visualstudio.com/download).
2. Install the [Microsoft Python extension](https://marketplace.visualstudio.com/items?itemName=ms-python.python) in VS Code.
3. Install [Python 3.11.18](https://www.python.org/downloads/release/python-31118/) (recommended). The code uses Python 3.10+ syntax; use Python 3.10–3.12 with the pinned MediaPipe package.
4. Install [Arduino IDE 2](https://www.arduino.cc/en/software). This is needed later for the camera and display boards; you can begin the webcam demo before configuring Arduino.

### 2. Make the Python environment and download the pretrained model

In VS Code, open this project folder, then choose **Terminal > New Terminal**. Run these commands from the project folder on macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
cp .env.example .env
```

In VS Code, choose **Python: Select Interpreter** from the Command Palette and select the `.venv` environment. Then download Google's **Pose Landmarker Lite** task bundle using the included script:

```bash
python scripts/download_model.py --variant lite
```

The script saves `models/pose_landmarker_lite.task`. You can also [download the model directly](https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/1/pose_landmarker_lite.task) and save it with that exact filename in `models/`. MediaPipe uses this pretrained model to find a person's 33 pose landmarks; it is distinct from UI-PRMD exercise data. The project pins MediaPipe 0.10.21 for a consistent Python Tasks API. See Google's [Pose Landmarker guide](https://ai.google.dev/edge/mediapipe/solutions/vision/pose_landmarker/python).

### 3. Download UI-PRMD research data if you want to inspect it

Your team's numerical squat rules are transcribed and used by the program from [`data/research_rules.json`](data/research_rules.json); their explanation and the other exercise notes are in [`data/research_rules.md`](data/research_rules.md). Those values came from the research page. The raw UI-PRMD archive is optional for the live demo and is useful if the team wants to inspect the dataset and discuss whether the rules are reasonable. The dataset contains Vicon/Kinect positions and angles for 10 healthy subjects, including deep squats and intentionally suboptimal examples. [Dataset record and all files](https://zenodo.org/records/23104965)

For a first offline review, download just these two archives rather than all of the 1.3 GB record:

- [Segmented Movements.zip (about 207 MB)](https://zenodo.org/records/23104965/files/Segmented%20Movements.zip?download=1)
- [Incorrect Segmented Movements.zip (about 214 MB)](https://zenodo.org/records/23104965/files/Incorrect%20Segmented%20Movements.zip?download=1)

After downloading, extract both inside `data/ui_prmd/`. Look for filenames beginning with `m01` for deep squat. Do not add the archives or extracted files to Git. The raw dataset uses Vicon/Kinect coordinates, which differ from MediaPipe image landmarks; treat comparisons as offline research, not direct threshold transfer. More details are in [data/README.md](data/README.md).

## Folder organization

Keep the source files in the opened project folder. The setup should look like this after the first run:

```text
team27-exercise-tracker/
├── .env                              # local camera/serial settings; never commit
├── .venv/                            # Python packages; never commit
├── models/pose_landmarker_lite.task  # pretrained model; never commit
├── data/research_rules.json          # included research-note data used by code
├── data/ui_prmd/                     # optional extracted dataset; never commit
├── camera/.../secrets.h              # local Wi-Fi credentials; never commit
└── src/, scripts/, arduino/          # source code to commit
```

The `.gitignore` is already set to exclude `.env`, `.venv/`, `models/*.task`, `data/ui_prmd/`, and the real Wi-Fi credentials file.

## Get the prototype running before connecting hardware

The quickest demo uses the laptop webcam and the downloaded model. In VS Code's terminal, activate `.venv` if needed, make sure `.env` still has `CAMERA_SOURCE=0`, and run:

```bash
python -m src.main --source 0
```

This opens a preview window and runs pose estimation on the default webcam. On macOS, if asked, allow **Code** (Visual Studio Code) to use the camera in **System Settings > Privacy & Security > Camera**, then restart VS Code. Stand side-on with your whole body visible and hold a still upright stance for the first 30 frames. The preview shows the skeleton, count, state, and feedback; press `q` to quit. The Arduino output is optional and disabled while `SERIAL_PORT=` is empty. This is the first working prototype path; the ESP32 and OLED are integration steps after the laptop demo runs.

If you are using Windows, create the venv with `py -3.11 -m venv .venv` and activate it with `.venv\\Scripts\\activate` instead of the macOS `source` command.

## Add the ESP32-CAM stream

Install ESP32 support in Arduino IDE using Espressif's [official installation instructions](https://docs.espressif.com/projects/arduino-esp32/en/latest/installing.html). The stable Boards Manager URL is `https://espressif.github.io/arduino-esp32/package_esp32_index.json`.

Then flash the team camera:

1. Copy `camera/esp32_cam_stream/secrets.h.example` to `camera/esp32_cam_stream/secrets.h` and enter the 2.4 GHz Wi-Fi name and password. The real credentials file is ignored by Git.
2. Open `camera/esp32_cam_stream/esp32_cam_stream.ino` in Arduino IDE, select **AI Thinker ESP32-CAM**, and connect IO0 to GND to enter upload mode.
3. Upload the sketch, disconnect IO0 from GND, and press the board's Reset button.
4. Open Serial Monitor at 115200 baud to read the camera IP. The laptop and camera must be on the same Wi-Fi network.
5. Set `CAMERA_SOURCE` in `.env` to `http://<camera-ip>:81/stream`, then run the Python app again.

## Connect the Arduino display

The sketch assumes a 128×64 I2C SSD1306 OLED at its common I2C address and two optional external LEDs:

| Part | Uno R4 Minima connection |
| --- | --- |
| OLED SDA | SDA (A4 on the board header) |
| OLED SCL | SCL (A5 on the board header) |
| OLED VCC / GND | Match the OLED module's specified supply and GND |
| Green LED | D8 through a 220–330 Ω resistor to GND |
| Red LED | D9 through a 220–330 Ω resistor to GND |

In Arduino IDE Boards Manager install **Arduino UNO R4 Boards** (see [Arduino's setup guide](https://docs.arduino.cc/tutorials/uno-r4-minima/minima-getting-started)). Install the [U8g2 library](https://github.com/olikraus/u8g2) through Library Manager. Open `arduino/uno_r4_display/uno_r4_display.ino`, select Arduino Uno R4 Minima, and upload. Find its port in Arduino IDE under **Tools > Port**, close Serial Monitor, set `SERIAL_PORT` in `.env`, and restart the Python app. If your OLED is not an SSD1306 128×64 I2C module, change the U8g2 constructor to match its controller and size.

The Python-to-Arduino serial line is ASCII, newline-delimited:

```text
<valid_rep_count>|<status>|<short_feedback>
```

Example: `2|DEPTH|Squat deeper`. The Arduino sketch parses this protocol and updates the OLED and LEDs.

## Move the source to your teammate's computer

Commit the 18 source/setup files to GitHub. Do not commit `.env`, `secrets.h`, `.venv/`, `models/*.task`, or `data/ui_prmd/`. On the other computer, recreate the Python environment, run the model download script, copy `.env.example` to `.env`, and set that machine's camera and serial ports. Hardware ports and Wi-Fi settings are local to each machine.

## Raspberry Pi note

Google provides a [Raspberry Pi Pose Landmarker example](https://github.com/google-ai-edge/mediapipe-samples/tree/main/examples/pose_landmarker/raspberry_pi), but the Zero 2 W has 512 MB RAM and a 1 GHz quad-core CPU. The team brief correctly treats the Pi as something to measure before relying on it. First run the pipeline on the laptop; then benchmark the Zero 2 W with the live camera at QVGA and record frames per second, CPU load, memory use, and dropped frames. If the board cannot keep the feedback responsive, move pose inference to a more capable Pi while keeping this serial/display protocol.

## What the code does not claim

- MediaPipe estimates landmarks; the simple rules in this prototype do not diagnose a condition or guarantee safe form.
- The active squat thresholds come from the team's research notes; the exact transcription is in `data/research_rules.json` and `data/research_rules.md`.
- The app processes one person at a time and does not store or upload video or landmark logs.

If MediaPipe reports that it cannot create an OpenGL pixel format before opening the webcam, that is a machine/runtime graphics setup issue rather than a threshold-setting issue. Run from the normal VS Code desktop terminal, make sure VS Code has camera permission, and use the pinned dependency in a fresh `.venv`. The Codex command runner used to prepare this project did not expose the required OpenGL service, so I could download the model and install the dependencies here but could not confirm pose inference in that isolated runner.
