#include <Arduino.h>
#include <esp_sleep.h>

ulong interval_us = 100000;
ulong last_timestamp_us = 0;
int step_num = 0;
int max_step = 120;


void step() {
  Serial.printf("step %d, ts=%ld\n", step_num, last_timestamp_us);
}

bool done() {
  return step_num > max_step;
}

void shutdown() {
  Serial.println("shutdown");
  Serial.println();
  esp_deep_sleep_start();
}

void setup() {
  // put your setup code here, to run once:
  Serial.begin(115200);
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
    step_num++;
    step();
  }
  // If we are done shutdown the esp32
  if (done()) {
    shutdown();
  }
}
