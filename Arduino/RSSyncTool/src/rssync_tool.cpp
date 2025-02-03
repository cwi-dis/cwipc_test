#include <Arduino.h>
#include <esp_sleep.h>
#include <Adafruit_NeoPixel.h>
#include "rssync_tool.h"
#include "iotsaConfigFile.h"

#define PIN_SYNC_IN 3
#define PIN_SYNC_OUT_REALSENSE 0
#define PIN_SYNC_OUT_GENLOCK 1

// Realsense documentation (https://dev.intelrealsense.com/docs/multiple-depth-cameras-configuration)
// says the pulse duration is 100 microseconds. Assume this is the mimimum pulse duration, so use
// a bit more.
const unsigned long realsense_pulse_duration = 200;

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
hw_timer_t * free_timer = NULL;

// Free-running interval in microseconds
unsigned long free_interval = 0;
// Free-running next trigger time in microseconds
unsigned long free_next_micros = 0;

// Flag to remember whether input interrupt is configured.
bool input_interrupt_configured = false;

// Last input trigger time (microseconds)
unsigned long last_input_micros = 0;
int cur_input_count = 0;

// Last output trigger time (microseconds)
unsigned long last_output_micros = 0;
// When to reset the realsense output (microseconds)
unsigned long realsense_reset_micros = 0;
// When to reset the genlock output (microseconds)
unsigned long genlock_reset_micros = 0;

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


// Static function to handle the output trigger
void outputSyncPulse() {
  unsigned long now = micros();
  if (last_output_micros == 0) {
    // The first output pulse we don't generate, we just record the time
    // so when we output a pulse we can calculate the FPS and also the duration.
    last_output_micros = now;
    return;
  }
  unsigned long delta = now - last_output_micros;
  fps_out = 1000000.0 / delta;
  // IotsaSerial.printf("Output trigger: %ld %ld %f\n", now, delta, fps_out);
  last_output_micros = now;
  unsigned long genlock_pulse_duration = delta / 3;
  digitalWrite(PIN_SYNC_OUT_REALSENSE, HIGH);
  digitalWrite(PIN_SYNC_OUT_GENLOCK, HIGH);
  genlock_reset_micros = now + genlock_pulse_duration;
  realsense_reset_micros = now + realsense_pulse_duration;

}

// Static function to handle the input trigger
void inputTrigger() {
  unsigned long now = micros();
  if (last_input_micros > 0) {
    unsigned long delta = now - last_input_micros;
    fps_in = 1000000.0 / delta;
    // IotsaSerial.printf("Input trigger: %ld %ld %f\n", now, delta, fps_in);
  }
  last_input_micros = now;
  cur_input_count++;
  if (cur_input_count >= divider) {
    cur_input_count = 0;
    outputSyncPulse();
  } 
}

void IotsaRSSyncToolMod::setup() {
  pinMode(PIN_SYNC_OUT_REALSENSE, OUTPUT);
  pinMode(PIN_SYNC_OUT_GENLOCK, OUTPUT);
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
  // Clear the old timer or interrupt
  if (free_timer) {
    timerAlarmDisable(free_timer);
    timerDetachInterrupt(free_timer);
    timerEnd(free_timer);
    free_timer = NULL;
  }
  if (input_interrupt_configured) {
    detachInterrupt(PIN_SYNC_IN);
    input_interrupt_configured = false;
  }
  // Now setup the timer or the interrupt
  if (syncsource == FREE) {
    free_timer = timerBegin(0, 80, true);
    timerAttachInterrupt(free_timer, inputTrigger, true);
    timerAlarmWrite(free_timer, free_interval, true);
    timerAlarmEnable(free_timer);
  } else {
    // Realsense or Genlock. Hope these can be handled identically.
    pinMode(PIN_SYNC_IN, INPUT);
    attachInterrupt(PIN_SYNC_IN, inputTrigger, RISING);
    input_interrupt_configured = true;
  }
  
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
  if (server->hasArg("fps_free")) {
    float s_fps_free = server->arg("fps_free").toFloat();
    if (s_fps_free > 0) {
      fps_free = s_fps_free;
      anyChanged = true;
    } else {
      errorStr = "<p><em>Error: Invalid fps_free</em></p>";
    }
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
  if (realsense_reset_micros > 0 && now >= realsense_reset_micros) {
    digitalWrite(PIN_SYNC_OUT_REALSENSE, LOW);
    realsense_reset_micros = 0;
  }
  if (genlock_reset_micros > 0 && now >= genlock_reset_micros) {
    digitalWrite(PIN_SYNC_OUT_GENLOCK, LOW);
    genlock_reset_micros = 0;
  }
  if (now >= display_next_micros) {
    if (last_input_micros < now - 1000000) {
      // No input triggers in the last second, assume we have no input signal
      fps_in = 0;
    }
    if (last_output_micros < now - 1000000) {
      // No output triggers in the last second, assume we have no output signal
      fps_out = 0;
    } 
    display_next_micros = now + display_interval;
    display.display(syncSourceToString(syncsource), fps_in, fps_out, divider);
  }
}
