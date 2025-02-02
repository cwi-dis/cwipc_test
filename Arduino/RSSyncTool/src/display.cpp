#include "display.h"

#include <U8g2lib.h>
#include <Wire.h>

#define SDA_PIN 5
#define SCL_PIN 6

U8G2_SSD1306_72X40_ER_F_HW_I2C u8g2(U8G2_R0, /* reset=*/ U8X8_PIN_NONE);   // EastRising 0.42" OLED
bool initialized = false;

static void initialize() {
  if (initialized) return;
  IotsaSerial.println("display: setup, pausing...");
  delay(4000);
  IotsaSerial.println("display: setup:");
  Wire.begin(SDA_PIN, SCL_PIN);
  u8g2.begin();
  initialized = true;
}

static void displayString(const char *msg1, const char *msg2, const char *msg3) {
  u8g2.clearBuffer();					// clear the internal memory
  u8g2.setFont(u8g2_font_ncenB08_tf);	// choose a suitable font
  if (msg1) u8g2.drawStr(0,10,msg1);	// write something to the internal memory
  if (msg2) u8g2.drawStr(0,23,msg2);	// write something to the internal memory
  if (msg3) u8g2.drawStr(0,36,msg3);	// write something to the internal memory
  u8g2.sendBuffer();					// transfer internal memory to the display
  if (msg1) IotsaSerial.printf("display: 1: %s\n", msg1);
  if (msg2) IotsaSerial.printf("display: 2: %s\n", msg2);
  if (msg3) IotsaSerial.printf("display: 3: %s\n", msg3);
}

void DisplayMod::setup() {
    initialize();
}

//    void serverSetup() override;
void DisplayMod::loop() {

}

//    String info() override;
void DisplayMod::display(const char *syncsource, float fps_in, float fps_out, int divider) {
    initialize();
    char buf_in[16], buf_out[16];
    snprintf(buf_in, sizeof(buf_in), "%5.2f FPS", fps_in);
    snprintf(buf_out, sizeof(buf_out), "%5.2f FPS", fps_out);
    displayString(syncsource, buf_in, buf_out);
}
