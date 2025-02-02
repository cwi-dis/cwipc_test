#pragma once
#include "iotsa.h"
#include "display.h"

class IotsaRSSyncToolMod : public IotsaMod {
public:
    IotsaRSSyncToolMod(IotsaApplication &_app, DisplayInterface& _display) 
    : IotsaMod(_app), 
      display(_display) 
    {}
    void setup() override;
    void serverSetup() override;
    void loop() override;
    String info() override;
protected:
    DisplayInterface& display;
    void configLoad() override;
    void configSave() override;
private:
    void handler();
    void update_vars();
};
