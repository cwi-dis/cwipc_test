#include <Arduino.h>
#include <esp_sleep.h>

ulong interval_us = 1000;
ulong last_timestamp_us = 0;
uint32_t step_num = 0;
int print_step_interval = 1000;
int max_step = 100000;


uint32_t grayValue;
uint8_t grayBits[32];

void step() {
  step_num++;
  grayValue = step_num ^ (step_num >> 1);
  uint32_t tmpGray = grayValue;
  for(int i=0; i<32; i++) {
    grayBits[i] = tmpGray & 1;
    tmpGray >>= 1;
  }
  if (step_num % print_step_interval == 0) {
    Serial.printf("step %4d, gray %d%d%d%d%d%d%d%d%d%d%d%d%d%d%d%d\n", step_num, grayBits[0],grayBits[1],grayBits[2],grayBits[3],grayBits[4],grayBits[5],grayBits[6],grayBits[7],grayBits[8],grayBits[9],grayBits[10],grayBits[11],grayBits[12],grayBits[13],grayBits[14],grayBits[15]);
}
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
    step();
  }
  // If we are done shutdown the esp32
  if (done()) {
    shutdown();
  }
}
