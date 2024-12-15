#include <Arduino.h>
#include <esp_sleep.h>
#include <Adafruit_NeoPixel.h>
#include "rssync_tool.h"
#include "iotsaConfigFile.h"

void IotsaRSSyncToolMod::setup() {
  // put your setup code here, to run once:
  configLoad();
}
void IotsaRSSyncToolMod::serverSetup() {
  server->on("/rssynctool", std::bind(&IotsaRSSyncToolMod::handler, this));
}

void IotsaRSSyncToolMod::configLoad() {
  IotsaConfigFileLoad cf("/config/rssynctool.cfg");
  update_vars();
}

void IotsaRSSyncToolMod::configSave() {
  IotsaConfigFileSave cf("/config/rssynctool.cfg");

  update_vars();
}

void IotsaRSSyncToolMod::update_vars() {
}

String IotsaRSSyncToolMod::info() {
  String message = "<p>Convert RealSense sync signal to genlock.<br>See <a href=\"/rssynctool\">/rssynctool</a> to change settings</p>";
  return message;
};

void IotsaRSSyncToolMod::handler() 
{
  bool anyChanged = false;
  if (server->hasArg("RED_I")) {
    // RED_I = server->arg("RED_I").toInt();
    anyChanged = true;
  }

  if (anyChanged) {
    configSave();
  }
#if 0
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
#endif
};

void IotsaRSSyncToolMod::loop() {

}
