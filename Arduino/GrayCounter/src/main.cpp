#include "iotsa.h"
#include "iotsaWifi.h"
#include "iotsaOta.h"
#include "gray_counter.h"

// CHANGE: Add application includes and declarations here

#define WITH_OTA    // Enable Over The Air updates from ArduinoIDE. Needs at least 1MB flash.

IotsaApplication application("Greycode Video Synchronization");
IotsaWifiMod wifiMod(application);
IotsaOtaMod otaMod(application);
IotsaGraycounterMod graycounterMod(application);

// Standard setup() method, hands off most work to the application framework
void setup(void){
  application.setup();
  application.serverSetup();
}
 
// Standard loop() routine, hands off most work to the application framework
void loop(void){
  application.loop();
}

