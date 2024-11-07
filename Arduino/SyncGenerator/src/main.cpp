#include <Arduino.h>

// Which GPIO pin is used as output?
const int DIGITAL_PIN = 12;
const int ANALOG_PIN = 25;

const float fps = 25.0;
const float duty_cycle = 0.33;
const float analog_voltage = 1.8;

int analog_one_level;

ulong period_us;
ulong period_us_on;
ulong period_us_off;

ulong next_flip;
bool is_on;

void output(int on) {
  // printf("%d at %ld\n", on, millis());
  digitalWrite(DIGITAL_PIN, on);
  dacWrite(ANALOG_PIN, on?analog_one_level:0);
}

void setup() {
  Serial.begin(115200);
  period_us = (ulong)(1000000L / fps);
  period_us_on = (ulong)(period_us * duty_cycle);
  period_us_off = period_us - period_us_on;
  analog_one_level = 255 * (analog_voltage/3.3);
  printf("SyncGenerator: fps=%f, duty_cycle=%f, period=%ld, on=%ld, off=%ld, analogvolt=%f, analoglevel=%d\n", fps, duty_cycle, period_us, period_us_on, period_us_off, analog_voltage, analog_one_level);
  pinMode(DIGITAL_PIN, OUTPUT);
}

void loop() {
  // put your main code here, to run repeatedly:
  ulong now_us = micros();
  if (now_us < next_flip) return;
  if (is_on) {
    output(0);
    is_on = false;
    next_flip = now_us + period_us_off;
  } else {
    output(1);
    is_on = true;
    next_flip = now_us + period_us_on;
  }
  // Need to cater for microsecond counter wraparound
  if (next_flip < now_us) {
    delayMicroseconds(period_us);
  }
}
