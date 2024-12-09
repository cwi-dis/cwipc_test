#include <Arduino.h>
#include <esp_sleep.h>
#include <Adafruit_NeoPixel.h>
#include "gray_counter.h"
#include "iotsaConfigFile.h"

// Which GPIO pin on the esp32 is connected to the NeoPixels?
const int PIN = 12;

// Which GPIO pin is used for sourcing power to the strip?
const int POWER_PIN = 13;

// Which pin is 
// How many NeoPixels are attached? The first pixel is red, the last pixel is blue,
// to allow finding the strip automatically. So the Gray
// code will be displayed in NUMPIXELS-2 bits.
const int NUMPIXELS = 18;

// Intensity values (0..255) for red, green and blue pixels.
// Select these values so the colors are bright enough so the cameras can see them,
// but not so bright the color is drowned out.
int RED_I = 32;
int GREEN_I = 32;
int BLUE_I = 32;

// Target frame rate, and interval in microseconds between changes in pattern (computed as 1/(2*fps))
float target_fps = 30;
ulong interval_us = 0;

// Interval in seconds between "clapboard" flashes (All LEDs same color for 1/(fps/2) seconds)
int clapboard = 5;
ulong next_clapboard_ms = 0;

// After how many seconds will the esp32 power down? Reset every time the web interface is accessed.
int wake_duration = 60;
int sleep_after_millis_time = 0;

// Every so many steps we print something to serial (mainly for debugging)
int print_step_interval = 1000;

// Our neopixel strip
Adafruit_NeoPixel pixels(NUMPIXELS, PIN, NEO_GRB + NEO_KHZ800);

// Most recent pattern change time
ulong last_timestamp_us = 0;

// How many pattern changes we have done since startup. Note: must have more bits
// than the number 
uint32_t step_num = 0;

// Current gray code value (transcoding of step_num)
uint32_t grayValue;
// Individual bits of the current gray code
uint8_t grayBits[32];

void initPower() {
  pinMode(POWER_PIN, OUTPUT);
  gpio_set_drive_capability((gpio_num_t)POWER_PIN, GPIO_DRIVE_CAP_3);
  digitalWrite(POWER_PIN, 1);
}

void shutdownPower() {
  digitalWrite(POWER_PIN, 0);
  pinMode(POWER_PIN, INPUT);
}

void initStrip() {
  pixels.begin();
}

void shutdownStrip() {
  pixels.clear();
  pixels.show();
}

void refreshStrip() {
  uint32_t onColor = pixels.Color(0, GREEN_I, 0);
  pixels.clear();
  pixels.setPixelColor(0, pixels.Color(RED_I, 0, 0));
  pixels.setPixelColor(NUMPIXELS-1, pixels.Color(0, 0, BLUE_I));
  pixels.setPixelColor(2, pixels.Color(0, 0, 0));
  for(int i=1; i<NUMPIXELS-1; i++) {
    if (grayBits[i-1]) {
      pixels.setPixelColor(i, onColor);
    }
  }
  pixels.show();
}

void step() {
  step_num++;
  grayValue = step_num ^ (step_num >> 1);
  uint32_t tmpGray = grayValue;
  for(int i=0; i<32; i++) {
    grayBits[i] = tmpGray & 1;
    tmpGray >>= 1;
  }
  refreshStrip();
  if (step_num % print_step_interval == 0) {
    Serial.printf("step %4d, gray %d%d%d%d%d%d%d%d%d%d%d%d%d%d%d%d\n", step_num, grayBits[0],grayBits[1],grayBits[2],grayBits[3],grayBits[4],grayBits[5],grayBits[6],grayBits[7],grayBits[8],grayBits[9],grayBits[10],grayBits[11],grayBits[12],grayBits[13],grayBits[14],grayBits[15]);
}
}

bool done() {
  return millis() > sleep_after_millis_time;
}

void shutdown() {
  shutdownStrip();
  Serial.println("shutdown");
  Serial.println();
  shutdownPower();
  esp_deep_sleep_start();
}

void IotsaGraycounterMod::setup() {
  // put your setup code here, to run once:
  initPower();
  Serial.begin(115200);
  initStrip();
  configLoad();
}
void IotsaGraycounterMod::serverSetup() {
  server->on("/graycounter", std::bind(&IotsaGraycounterMod::handler, this));
}

void IotsaGraycounterMod::configLoad() {
  IotsaConfigFileLoad cf("/config/graycounter.cfg");
  cf.get("RED_I", RED_I, RED_I);
  cf.get("GREEN_I", GREEN_I, GREEN_I);
  cf.get("BLUE_I", BLUE_I, BLUE_I);
  cf.get("target_fps", target_fps, target_fps);
  cf.get("clapboard", clapboard, clapboard);
  cf.get("wake_duration", wake_duration, wake_duration);
  update_vars();
}

void IotsaGraycounterMod::configSave() {
  IotsaConfigFileSave cf("/config/graycounter.cfg");
  cf.put("RED_I", RED_I);
  cf.put("GREEN_I", GREEN_I);
  cf.put("BLUE_I", BLUE_I);
  cf.put("target_fps", target_fps);
  cf.put("clapboard", clapboard);
  cf.put("wake_duration", wake_duration);
  update_vars();
}

void IotsaGraycounterMod::update_vars() {
  interval_us = (ulong)(1000000.0 / (2*target_fps));
  next_clapboard_ms = millis() + (clapboard * 1000);
  sleep_after_millis_time = millis() + (wake_duration * 1000);
  IFDEBUG IotsaSerial.printf("interval_us=%ld, next_clapboard_ms=%ld, sleep_after_millis_time=%ld\n", interval_us, next_clapboard_ms, sleep_after_millis_time);
}

String IotsaGraycounterMod::info() {
  String message = "<p>Flashes a LED strip to allow determining whether multiple video cameras capture in sync.<br>See <a href=\"/graycounter\">/graycounter</a> to change settings</p>";
  return message;
};
void IotsaGraycounterMod::handler() 
{
  bool anyChanged = false;
  if (server->hasArg("RED_I")) {
    RED_I = server->arg("RED_I").toInt();
    anyChanged = true;
  }
  if (server->hasArg("GREEN_I")) {
    GREEN_I = server->arg("GREEN_I").toInt();
    anyChanged = true;
  }
  if (server->hasArg("BLUE_I")) {
    BLUE_I = server->arg("BLUE_I").toInt();
    anyChanged = true;
  }
  if (server->hasArg("target_fps")) {
    target_fps = server->arg("target_fps").toFloat();
    anyChanged = true;
  }
  if (server->hasArg("clapboard")) {
    clapboard = server->arg("clapboard").toInt();
    anyChanged = true;
  }
  if (server->hasArg("wake_duration")) {
    wake_duration = server->arg("wake_duration").toInt();
    anyChanged = true;
  }
  if (anyChanged) {
    configSave();
  }
  String message = "<html><head><title>Graycounter configuration</title></head><body><h1>Graycounter configuration</h1>";
  message += "<form method='get'>";
  message += "<h3>LED brightness</h3>";
  message += "Intensity R: <input name='RED_I' value='" + String(RED_I) + "'><br>";
  message += "Intensity G: <input name='GREEN_I' value='" + String(GREEN_I) + "'><br>";
  message += "Intensity B: <input name='BLUE_I' value='" + String(BLUE_I) + "'><br>";
  message += "<h3>Pattern timing</h3>";
  message += "Target frame rate: <input name='target_fps' value='" + String(target_fps) + "'>";
  message += "<I>(pattern will change at twice this rate)</i><br>";
  message += "Clapboard interval: <input name='clapboard' value='" + String(clapboard) + "'>";
  message += "<I>(Every so many seconds all LEDs will be the same color for 2 frame durations)</I><br>";
  message += "<h3>Power saving</h3>";
  message += "Wake duration: <input name='wake_duration' value='" + String(wake_duration) + "'>";
  message += "<I>(After this many seconds the device will power off)</I><br>";
  message += "<br>";
  message += "<input type='submit'></form>";
  server->send(200, "text/html", message);
  update_vars(); // Really only needs to set the sleep time...
};

void IotsaGraycounterMod::loop() {
  // put your main code here, to run repeatedly:
  ulong now_us = micros();
  if (now_us < last_timestamp_us) {
    // Microsecond clock has wrapped.
    last_timestamp_us = 0;
  }
  if (now_us > last_timestamp_us + interval_us) {
    // Time to do a next step
    last_timestamp_us = now_us;
    step();
  }
  // If we are done shutdown the esp32
  if (done()) {
    shutdown();
  }
}
