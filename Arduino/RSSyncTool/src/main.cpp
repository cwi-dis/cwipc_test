#include "iotsa.h"
#include "iotsaWifi.h"
#include "iotsaOta.h"
#include "rssync_tool.h"
#include "display.h"

// CHANGE: Add application includes and declarations here

#define WITH_OTA    // Enable Over The Air updates from ArduinoIDE. Needs at least 1MB flash.

IotsaApplication application("RealSense Sync Converter");
IotsaWifiMod wifiMod(application);
DisplayMod displayMod(application);
IotsaRSSyncToolMod rssynctoolMod(application, displayMod);

// Standard setup() method, hands off most work to the application framework
void setup(void){
  application.setup();
  application.serverSetup();
}
 
// Standard loop() routine, hands off most work to the application framework
void loop(void){
  application.loop();
}

