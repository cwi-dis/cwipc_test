# Millisecond Gray code counter

This project drives an 18-LED NeoPixel strip to show a pattern that changes every millisecond. Moreover, each pattern will differ **in only one led** from the previous pattern.

This means that if you capture the strip with two cameras that _should_ be frame accurately synchronized you can determine whether this is actually the case: if the frame duration is less than `2**x ms` at most `x` LEDs may have a different value (or an indeterminate half-on-half-off value).

## Construction

As-is the project uses a _Lolin 32 Lite_ ESP32 board. This board was selected because it can be operated from a lipo battery, and has an on-board charger.

You need an 18 LED NeoPixel strip, 60 LEDs per meter or even 30 LEDs per meter preferred. Connect

- strip GND to Lolin GND, 
- strip 5V to Lolin GPIO 13 (_indeed!_), 
- strip DATA-IN to GPIO 12. 

Powering the strip through GPIO 13 will shut off power to the strip when the esp32 hibernates. This saves approximately 20mA (the neopixels use a little over a milliamp when powered and not active.

Build the project with `platformio` and flash it to the board. On reboot it should go through a full 65 second sequence.

You probably want a lipo battery, so you do not have to power the board. t is nice to have a pushbutton for _Reset_, connect between _EN_ and _GND_. 

Below is a picture of the assembled board:

![Assembled board](hardware/board-construction.jpeg)

If you want to get fancy you can 3D print a case. In directory `hardware/3dmodel` you find the needed files. You can directly print `Housing.stl` and `Lid.stl`, or you can import `SyncLedStripHousing.f3d` into _Fusion 3D` and modify it for your needs.

![Board complete with housing](hardware/complete.jpeg)

There is also a `LedStripBase.stl` and the accompanying `.f3d`, if you print two of these and glue the strip to it you can be sure they are in a straight line.

We have found that using a permanent marker to make the strips as black as possible (with the exception of the LED windows, obviously) helps detection.

Here is the complete result:
![Board in operation](hardware/inoperation.jpeg)

## Use

Charge the lipo.

When you `RESET` the board it will go through the whole sequence, and after 65532 steps (just over a minute) it will go to deep sleep. It will also power down the NeoPixel strip, so power consumption should be absolutely minimal (micro-amps).

The first and last LEDs are fixed: RED and BLUE. All other LEDs are either GREEN or OFF, and show the Gray code.

Maybe one day we will add the code to `cwipc_register` so that it can automatically find the LED strips in the captured RGB images, but for now you have do this yourself (you, the human):

- Capture a set of RGB images, one from each camera, that you expect to be synchronized.
- if `N` low-order pixels (near the red marker) are different the pictures were captured `2**N` milliseconds apart.
- In other words: if you are capturing at `30fps` you expect at most 5 low order pixels to be different, and no high order pixels.

  > This is not completely true, technically, because at some points in time a high order pixel will flip. Then you expect at most 4 low order pixels to be different. Read up on Gray code if you want to know more.