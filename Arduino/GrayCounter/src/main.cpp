#include <Arduino.h>
#include <esp_sleep.h>
#include <Adafruit_NeoPixel.h>

// Which pin on the Arduino is connected to the NeoPixels?
const int PIN = 12;

// How many NeoPixels are attached? The first 3 pixels are used with a fixed
// pattern (red, blue, off) to allow finding the strip automatically. So the Gray
// code will be displayed in NUMPIXELS-3 bits.
const int NUMPIXELS = 18;

// Intensity values (0..255) for red, green and blue pixels.
// Select these values so the colors are bright enough so the cameras can see them,
// but not so bright the color is drowned out.
const int RED_I = 8;
const int GREEN_I = 8;
const int BLUE_I = 8;

// Interval in microseconds between changes in pattern
const ulong interval_us = 1000;

// After how many intervals will the esp32 power down?
const int max_step = 65532;

// Every so many steps we print something to serial (mainly for debugging)
const int print_step_interval = 1000;

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
  pixels.setPixelColor(1, pixels.Color(0, 0, BLUE_I));
  pixels.setPixelColor(2, pixels.Color(0, 0, 0));
  for(int i=3; i<NUMPIXELS; i++) {
    if (grayBits[i-3]) {
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
  return step_num > max_step;
}

void shutdown() {
  shutdownStrip();
  Serial.println("shutdown");
  Serial.println();
  esp_deep_sleep_start();
}

void setup() {
  // put your setup code here, to run once:
  Serial.begin(115200);
  initStrip();
}

void loop() {
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
