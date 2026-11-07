// AI Thinker ESP32-CAM firmware: expose a local MJPEG stream at /stream on port 81.
// Copy secrets.h.example to secrets.h and enter Wi-Fi credentials before uploading.

#include "esp_camera.h"
#include <WiFi.h>
#include "esp_http_server.h"
#include "secrets.h"

// AI Thinker ESP32-CAM camera pins.
#define PWDN_GPIO_NUM     32
#define RESET_GPIO_NUM    -1
#define XCLK_GPIO_NUM      0
#define SIOD_GPIO_NUM     26
#define SIOC_GPIO_NUM     27
#define Y9_GPIO_NUM       35
#define Y8_GPIO_NUM       34
#define Y7_GPIO_NUM       39
#define Y6_GPIO_NUM       36
#define Y5_GPIO_NUM       21
#define Y4_GPIO_NUM       19
#define Y3_GPIO_NUM       18
#define Y2_GPIO_NUM        5
#define VSYNC_GPIO_NUM    25
#define HREF_GPIO_NUM     23
#define PCLK_GPIO_NUM     22

static httpd_handle_t status_httpd = nullptr;
static httpd_handle_t stream_httpd = nullptr;
static const char *STREAM_CONTENT_TYPE = "multipart/x-mixed-replace;boundary=frame";
static const char *STREAM_BOUNDARY = "\r\n--frame\r\n";
static const char *STREAM_PART = "Content-Type: image/jpeg\r\nContent-Length: %u\r\n\r\n";

static esp_err_t status_handler(httpd_req_t *request) {
  const char *message = "Team 27 ESP32-CAM ready. Stream: http://<camera-ip>:81/stream\n";
  httpd_resp_set_type(request, "text/plain");
  return httpd_resp_send(request, message, HTTPD_RESP_USE_STRLEN);
}

static esp_err_t stream_handler(httpd_req_t *request) {
  camera_fb_t *frame = nullptr;
  uint8_t *jpg_buffer = nullptr;
  size_t jpg_length = 0;
  char part_header[64];

  httpd_resp_set_type(request, STREAM_CONTENT_TYPE);
  httpd_resp_set_hdr(request, "Access-Control-Allow-Origin", "*");

  while (true) {
    frame = esp_camera_fb_get();
    if (frame == nullptr) {
      return ESP_FAIL;
    }

    if (frame->format == PIXFORMAT_JPEG) {
      jpg_buffer = frame->buf;
      jpg_length = frame->len;
    } else if (!frame2jpg(frame, 80, &jpg_buffer, &jpg_length)) {
      esp_camera_fb_return(frame);
      return ESP_FAIL;
    }

    esp_err_t result = httpd_resp_send_chunk(request, STREAM_BOUNDARY, strlen(STREAM_BOUNDARY));
    if (result == ESP_OK) {
      const size_t header_length = snprintf(part_header, sizeof(part_header), STREAM_PART, jpg_length);
      result = httpd_resp_send_chunk(request, part_header, header_length);
    }
    if (result == ESP_OK) {
      result = httpd_resp_send_chunk(request, reinterpret_cast<const char *>(jpg_buffer), jpg_length);
    }

    if (frame->format != PIXFORMAT_JPEG) {
      free(jpg_buffer);
      jpg_buffer = nullptr;
    }
    esp_camera_fb_return(frame);
    frame = nullptr;

    if (result != ESP_OK) {
      return result;
    }
  }
}

static void start_camera_servers() {
  httpd_config_t status_config = HTTPD_DEFAULT_CONFIG();
  status_config.server_port = 80;
  status_config.ctrl_port = 32768;
  httpd_uri_t status_uri = {
    .uri = "/",
    .method = HTTP_GET,
    .handler = status_handler,
    .user_ctx = nullptr
  };
  if (httpd_start(&status_httpd, &status_config) == ESP_OK) {
    httpd_register_uri_handler(status_httpd, &status_uri);
  }

  httpd_config_t stream_config = HTTPD_DEFAULT_CONFIG();
  stream_config.server_port = 81;
  stream_config.ctrl_port = 32769;
  httpd_uri_t stream_uri = {
    .uri = "/stream",
    .method = HTTP_GET,
    .handler = stream_handler,
    .user_ctx = nullptr
  };
  if (httpd_start(&stream_httpd, &stream_config) == ESP_OK) {
    httpd_register_uri_handler(stream_httpd, &stream_uri);
  }
}

void setup() {
  Serial.begin(115200);
  Serial.println();

  camera_config_t config = {};
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer = LEDC_TIMER_0;
  config.pin_d0 = Y2_GPIO_NUM;
  config.pin_d1 = Y3_GPIO_NUM;
  config.pin_d2 = Y4_GPIO_NUM;
  config.pin_d3 = Y5_GPIO_NUM;
  config.pin_d4 = Y6_GPIO_NUM;
  config.pin_d5 = Y7_GPIO_NUM;
  config.pin_d6 = Y8_GPIO_NUM;
  config.pin_d7 = Y9_GPIO_NUM;
  config.pin_xclk = XCLK_GPIO_NUM;
  config.pin_pclk = PCLK_GPIO_NUM;
  config.pin_vsync = VSYNC_GPIO_NUM;
  config.pin_href = HREF_GPIO_NUM;
  config.pin_sccb_sda = SIOD_GPIO_NUM;
  config.pin_sccb_scl = SIOC_GPIO_NUM;
  config.pin_pwdn = PWDN_GPIO_NUM;
  config.pin_reset = RESET_GPIO_NUM;
  config.xclk_freq_hz = 20000000;
  config.pixel_format = PIXFORMAT_JPEG;
  config.frame_size = FRAMESIZE_QVGA;
  config.jpeg_quality = 14;
  config.fb_count = 1;
  config.grab_mode = CAMERA_GRAB_LATEST;
  if (psramFound()) {
    config.fb_location = CAMERA_FB_IN_PSRAM;
    config.fb_count = 2;
  } else {
    config.fb_location = CAMERA_FB_IN_DRAM;
  }

  const esp_err_t camera_result = esp_camera_init(&config);
  if (camera_result != ESP_OK) {
    Serial.printf("Camera init failed: 0x%x\n", camera_result);
    return;
  }

  WiFi.mode(WIFI_STA);
  WiFi.setSleep(false);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  Serial.print("Connecting to Wi-Fi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println();
  Serial.print("Camera IP: ");
  Serial.println(WiFi.localIP());

  start_camera_servers();
  Serial.print("MJPEG stream: http://");
  Serial.print(WiFi.localIP());
  Serial.println(":81/stream");
}

void loop() {
  delay(1000);
}
