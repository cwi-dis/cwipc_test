#include "iotsa.h"

class IotsaGraycounterMod : public IotsaMod {
public:
    IotsaGraycounterMod(IotsaApplication &_app) : IotsaMod(_app) {}
    void setup() override;
    void serverSetup() override;
    void loop() override;
    String info() override;
protected:
    void configLoad() override;
    void configSave() override;
private:
    void handler();
    void update_vars();
};
