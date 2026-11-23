// Read Python's "mode|completed|status|feedback\n" messages and show them
// on the OLED/LEDs. A D2-to-GND button sends MODE_NEXT back to Python.
// Install U8g2 in Arduino IDE Library Manager before compiling this sketch.

#include <U8g2lib.h>

// Assumes a 128x64 SSD1306 I2C OLED. Change this constructor for another display.
U8G2_SSD1306_128X64_NONAME_F_HW_I2C display(U8G2_R0, U8X8_PIN_NONE);

const int GREEN_LED_PIN = 8;
const int RED_LED_PIN = 9;
const int MODE_BUTTON_PIN = 2;
int completedCount = 0;
String modeText = "DEEP SQUAT";
String statusText = "WAIT";
String feedbackText = "Waiting for Pi";
int lastButtonReading = HIGH;
int stableButtonState = HIGH;
unsigned long lastDebounceTime = 0;
const unsigned long DEBOUNCE_MS = 35;

static void update_from_line(const String &line) {
  const int firstSeparator = line.indexOf('|');
  const int secondSeparator = line.indexOf('|', firstSeparator + 1);
  const int thirdSeparator = line.indexOf('|', secondSeparator + 1);
  if (firstSeparator < 1 || secondSeparator <= firstSeparator || thirdSeparator <= secondSeparator) {
    return;
  }

  const String modeId = line.substring(0, firstSeparator);
  if (modeId == "deep_squat") modeText = "DEEP SQUAT";
  else if (modeId == "plank") modeText = "PLANK HOLD";
  else if (modeId == "bicep_curl") modeText = "BICEP CURL";
  else if (modeId == "arm_rainbow") modeText = "ARM RAINBOW";
  else if (modeId == "farmers_carry") modeText = "FARMER CARRY";
  else if (modeId == "good_morning") modeText = "GOOD MORNING";
  completedCount = line.substring(firstSeparator + 1, secondSeparator).toInt();
  statusText = line.substring(secondSeparator + 1, thirdSeparator);
  feedbackText = line.substring(thirdSeparator + 1);
}

static void draw_display() {
  display.clearBuffer();
  display.setFont(u8g2_font_6x12_tf);
  display.drawStr(0, 12, modeText.substring(0, 20).c_str());
  display.drawStr(0, 28, statusText.substring(0, 20).c_str());
  display.setFont(u8g2_font_ncenB14_tr);
  char countText[20];
  snprintf(countText, sizeof(countText), "DONE %d", completedCount);
  display.drawStr(0, 50, countText);
  display.setFont(u8g2_font_5x8_tf);
  display.drawStr(0, 62, feedbackText.substring(0, 24).c_str());
  display.sendBuffer();
}

static void update_leds() {
  const bool good = statusText == "GOOD";
  const bool needsCorrection = statusText == "DEPTH" || statusText == "HIPS" || statusText == "HEAD" ||
    statusText == "TOO_LOW" || statusText == "TOO_HIGH" || statusText == "POSTURE" ||
    statusText == "LEGS" || statusText == "TOO_FAR";
  digitalWrite(GREEN_LED_PIN, good ? HIGH : LOW);
  digitalWrite(RED_LED_PIN, needsCorrection ? HIGH : LOW);
}

static void handle_mode_button() {
  const int reading = digitalRead(MODE_BUTTON_PIN);
  if (reading != lastButtonReading) {
    lastDebounceTime = millis();
  }
  if ((millis() - lastDebounceTime) > DEBOUNCE_MS && reading != stableButtonState) {
    stableButtonState = reading;
    if (stableButtonState == LOW) {
      Serial.println("MODE_NEXT");
    }
  }
  lastButtonReading = reading;
}

void setup() {
  pinMode(MODE_BUTTON_PIN, INPUT_PULLUP);
  pinMode(GREEN_LED_PIN, OUTPUT);
  pinMode(RED_LED_PIN, OUTPUT);
  digitalWrite(GREEN_LED_PIN, LOW);
  digitalWrite(RED_LED_PIN, LOW);
  Serial.begin(115200);
  Serial.setTimeout(50);
  display.begin();
  display.setBusClock(400000);  // fast I2C so a redraw takes ~25 ms instead of ~90 ms
  draw_display();
}

void loop() {
  handle_mode_button();
  // Drain every waiting line first, then redraw once with the newest data so
  // slow screen redraws never let the USB buffer back up and drop messages.
  bool updated = false;
  while (Serial.available() > 0) {
    String line = Serial.readStringUntil('\n');
    line.trim();
    if (line.length() > 0) {
      update_from_line(line);
      updated = true;
    }
    handle_mode_button();
  }
  if (updated) {
    update_leds();
    draw_display();
  }
}
