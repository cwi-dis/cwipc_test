#include <Arduino.h>
#include <esp_sleep.h>
#include <Adafruit_NeoPixel.h>
#include "rssync_tool.h"
#include "iotsaConfigFile.h"

// Current incoming FPS (frames per second)
float fps_in;
// Divider between fps_in and fps_out
int divider = 1;
// Current outgoing FPS (frames per second)
float fps_out;

void IotsaRSSyncToolMod::setup() {
  // put your setup code here, to run once:
  configLoad();
}
void IotsaRSSyncToolMod::serverSetup() {
  server->on("/rssynctool", std::bind(&IotsaRSSyncToolMod::handler, this));
}

void IotsaRSSyncToolMod::configLoad() {
  IotsaConfigFileLoad cf("/config/rssynctool.cfg");
  cf.get("divider", divider, divider);
  update_vars();
}

void IotsaRSSyncToolMod::configSave() {
  IotsaConfigFileSave cf("/config/rssynctool.cfg");
  cf.put("divider", divider);
  update_vars();
}

void IotsaRSSyncToolMod::update_vars() {
}

String IotsaRSSyncToolMod::info() {
  String message = "<p>Convert RealSense sync signal to genlock.<br>See <a href=\"/rssynctool\">/rssynctool</a> to change settings.<br>";
  message += "Current incoming Realsense sync signal: " + String(fps_in) + "fps.<br>";
  message += "Current outgoing genlock sync signal: " + String(fps_out) + "fps.<br>";
  message += "</p>";
  return message;
};

void IotsaRSSyncToolMod::handler() 
{
  bool anyChanged = false;
  if (server->hasArg("divider")) {
    divider = server->arg("divider").toInt();
    anyChanged = true;
  }

  if (anyChanged) {
    configSave();
  }
  String message = "<html><head><title>Sync generator configuration</title></head><body><h1>Sync generator configuration</h1>";
  message += "<form method='get'>";
  message += "Divider: <input name='divider' value='" + String(divider) + "'><br>";
  message += "<br>";
  message += "<input type='submit'></form>";
  server->send(200, "text/html", message);
  update_vars(); // Really only needs to set the sleep time...
};

void IotsaRSSyncToolMod::loop() {

}
