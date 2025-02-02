#include <Arduino.h>
#include <esp_sleep.h>
#include <Adafruit_NeoPixel.h>
#include "rssync_tool.h"
#include "iotsaConfigFile.h"

enum SyncSource {
  FREE,
  REALSENSE,
  GENLOCK
};

inline const char *syncSourceToString(enum SyncSource syncsource) {
  switch(syncsource) {
    case FREE: return "Free";
    case REALSENSE: return "RealSense";
    case GENLOCK: return "Genlock";
  }
  return "Unknown";
}

enum SyncSource syncsource = FREE;

// FPS when free-running
float fps_free = 29.97;

// Free-running interval in microseconds
unsigned long free_interval = 0;
// Free-running next trigger time in microseconds
unsigned long free_next_micros = 0;

// Last input trigger time (microseconds)
unsigned long last_input_micros = 0;

// How often to update the display (microseconds)
unsigned long display_interval = 1000000;
// When to display next (microseconds)
unsigned long display_next_micros = 0;
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
  int s_syncsource;
  cf.get("syncsource", s_syncsource, (int)syncsource);
  syncsource = (enum SyncSource)s_syncsource;
  cf.get("fps_free", fps_free, fps_free);
  cf.get("divider", divider, divider);
  update_vars();
}

void IotsaRSSyncToolMod::configSave() {
  IotsaConfigFileSave cf("/config/rssynctool.cfg");
  cf.put("syncsource", (int)syncsource);
  cf.put("fps_free", fps_free);
  cf.put("divider", divider);
  update_vars();
}

void IotsaRSSyncToolMod::update_vars() {
  free_interval = 1000000 / fps_free;
  free_next_micros = 0;
  fps_in = 0;
  fps_out = 0;
  last_input_micros = micros();
  display_next_micros = 0;
}

String IotsaRSSyncToolMod::info() {
  String message = "<p>Convert RealSense sync signal to genlock.<br>See <a href=\"/rssynctool\">/rssynctool</a> to change settings.<br>";
  message += "Current sync source: " + String(syncSourceToString(syncsource)) + ".<br>";
  message += "Current incoming sync signal: " + String(fps_in) + "fps.<br>";
  message += "Current outgoing sync signal: " + String(fps_out) + "fps.<br>";
  message += "</p>";
  return message;
};

void IotsaRSSyncToolMod::handler() 
{
  const char *errorStr = nullptr;
  bool anyChanged = false;
  if (server->hasArg("divider")) {
    divider = server->arg("divider").toInt();
    anyChanged = true;
  }
  if (server->hasArg("syncsource")) {
    int s_syncsource = server->arg("syncsource").toInt();
    if (s_syncsource >= 0 && s_syncsource <= 2) {
      syncsource = (enum SyncSource)s_syncsource;
      anyChanged = true;
    } else {
      errorStr = "<p><em>Error: Invalid sync source</em></p>";
    }
  } 
  if (anyChanged) {
    configSave();
  }
  String message = "<html><head><title>Sync generator configuration</title></head><body><h1>Sync generator configuration</h1>";
  if (errorStr) message += errorStr;
  message += "<form method='get'>";
  message += "Sync source: <select name='syncsource'>";
  for(int i=0; i<=2; i++) {
    message += "<option value='" + String(i) + "'";
    if (i == (int)syncsource) message += " selected";
    message += ">" + String(syncSourceToString((enum SyncSource)i)) + "</option>";
  }
  message += "</select><br>";
  message += "FPS when free-running: <input name='fps_free' value='" + String(fps_free) + "'><br>";
  message += "Divider: <input name='divider' value='" + String(divider) + "'><br>";
  message += "<br>";
  message += "<input type='submit'></form>";
  server->send(200, "text/html", message);
  update_vars(); // Really only needs to set the sleep time...
};

void IotsaRSSyncToolMod::loop() {
  unsigned long now = micros();
  if (syncsource == FREE) {
    if (now >= free_next_micros) {
      inputTrigger();
      if (free_next_micros > 0) {
        free_next_micros += free_interval;
      } else {
        free_next_micros = now + free_interval;
      }
    }
  }
  if (now >= display_next_micros) {
    display_next_micros = now + display_interval;
    display.display(syncSourceToString(syncsource), fps_in, fps_out, divider);
  }
}

void IotsaRSSyncToolMod::inputTrigger() {
  unsigned long now = micros();
  if (last_input_micros > 0) {
    unsigned long delta = now - last_input_micros;
    fps_in = 1000000.0 / delta;
    // IotsaSerial.printf("Input trigger: %ld %ld %f\n", now, delta, fps_in);
  }
  last_input_micros = now;
}

void IotsaRSSyncToolMod::outputSyncPulse() {

}