// Read Python's "rep_count|status|feedback\n" messages and show them on OLED/LEDs.
// Install U8g2 in Arduino IDE Library Manager before compiling this sketch.

#include <U8g2lib.h>

// Assumes a 128x64 SSD1306 I2C OLED. Change this constructor for another display.
U8G2_SSD1306_128X64_NONAME_F_HW_I2C display(U8G2_R0, U8X8_PIN_NONE);

const int GREEN_LED_PIN = 8;
const int RED_LED_PIN = 9;
int repCount = 0;
String statusText = "WAIT";
String feedbackText = "Waiting for Pi";

static void update_from_line(const String &line) {
  const int firstSeparator = line.indexOf('|');
  const int secondSeparator = line.indexOf('|', firstSeparator + 1);
  if (firstSeparator < 1 || secondSeparator <= firstSeparator) {
    return;
  }

  repCount = line.substring(0, firstSeparator).toInt();
  statusText = line.substring(firstSeparator + 1, secondSeparator);
  feedbackText = line.substring(secondSeparator + 1);
}

static void draw_display() {
  display.clearBuffer();
  display.setFont(u8g2_font_6x12_tf);
  display.drawStr(0, 12, "DEEP SQUAT");
  display.drawStr(0, 28, statusText.substring(0, 20).c_str());
  display.setFont(u8g2_font_ncenB14_tr);
  char countText[20];
  snprintf(countText, sizeof(countText), "REPS %d", repCount);
  display.drawStr(0, 50, countText);
  display.setFont(u8g2_font_5x8_tf);
  display.drawStr(0, 62, feedbackText.substring(0, 24).c_str());
  display.sendBuffer();
}

static void update_leds() {
  const bool good = statusText == "GOOD";
  const bool needsCorrection = statusText == "DEPTH" || statusText == "HIPS" || statusText == "HEAD";
  digitalWrite(GREEN_LED_PIN, good ? HIGH : LOW);
  digitalWrite(RED_LED_PIN, needsCorrection ? HIGH : LOW);
}

void setup() {
  pinMode(GREEN_LED_PIN, OUTPUT);
  pinMode(RED_LED_PIN, OUTPUT);
  digitalWrite(GREEN_LED_PIN, LOW);
  digitalWrite(RED_LED_PIN, LOW);
  Serial.begin(115200);
  Serial.setTimeout(50);
  display.begin();
  draw_display();
}

void loop() {
  if (Serial.available() > 0) {
    String line = Serial.readStringUntil('\n');
    line.trim();
    update_from_line(line);
    update_leds();
    draw_display();
  }
}
