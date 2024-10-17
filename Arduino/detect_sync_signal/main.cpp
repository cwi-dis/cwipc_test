#include <Arduino.h>

unsigned long lastPulse = 0;
unsigned long currentPulse = 0;

void IRAM_ATTR pulseDetected() {
  lastPulse = millis();
}

void setup() {
  Serial.begin(57600);
  attachInterrupt(GPIO_NUM_34, pulseDetected, RISING);
}

void loop() {
  if (lastPulse != currentPulse) {
    unsigned long pulseLen = lastPulse - currentPulse;
    currentPulse = lastPulse;

    Serial.print("Last pulse length: ");
    Serial.println(pulseLen);
  }
}
