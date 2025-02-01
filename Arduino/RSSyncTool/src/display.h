#pragma once
#include "iotsa.h"

class DisplayInterface {
public:
    virtual void display(const char *syncsource, float fps_in, float fps_out, int divider) = 0;
};

class DisplayMod : public IotsaMod, public DisplayInterface {
public:
    DisplayMod(IotsaApplication &_app) : IotsaMod(_app) {}
    void setup() override;
    void serverSetup() override {};
    void loop() override;
    String info() override { return "";};
    virtual void display(const char *syncsource, float fps_in, float fps_out, int divider) override;
protected:
//    void configLoad() override;
//    void configSave() override;
private:
//    void handler();
//    void update_vars();
};
