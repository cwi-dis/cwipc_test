#include "iotsa.h"

class IotsaGraycounterMod : public IotsaMod {
public:
    IotsaGraycounterMod(IotsaApplication &_app) : IotsaMod(_app) {}
    void setup() override;
    void serverSetup() override;
    void loop() override;
    String info() override;
private:
    void handler();
};
