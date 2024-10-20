# Millisecond Gray code counter

This project drives a 19-LED NeoPixel strip to show a pattern that changes every millisecond. Moreover, each pattern will differ in only **one** led from the previous pattern.

This means that if you capture the strip with two cameras that _should_ be frame accurately synchronized you can determine whether this is actually the case: if the frame duration is less than `2**x ms` at most `x` LEDs may have a different value (or an indeterminate half-on-half-off value).

## Construction

As-is the project uses a _Lolin 32 Lite_ ESP32 board. This board was selected because it can be operated from a lipo battery, and has an on-board charger.

You need a 19 LED NeoPixel strip. Connect strip GND to Lolin GND, strip 5V to Lolin GPIO 13 (_indeed!_), strip DATA-IN to GPIO 12.

Build the project with `platformio` and flash it to the board. It should go through a full sequence.

## Use

Charge the lipo.

When you `RESET` the board it will go through the whole sequence, and after 65532 steps it will go to deep sleep. It will also power down the NeoPixel strip, so power consumption should be absolutely minimal (micro-amps).

The first three LEDs are fixed: RED, BLUE, OFF. All other LEDs are either GREEN or OFF, and show the Gray code.