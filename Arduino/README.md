# IOT helper programs

Not really only arduino.

`Neopixelsync` is a program that can be used to have a 16-pixel Neopixel strip flash a binary pattern in Gray Code, which changes every millisecond. Capturing this with multiple RGB cameras allows you to see whether the cameras are frame-accurately synced. But `GrayCounter` below is actually much better.

`Detect_sync_signal` will print out interval between rising pulses on GPIO 34. It can be used to detect the Realsense sync signal.

`GrayCounter` is a newer version of the gray-code millisecond counter that can be run off a battery. See [GrayCounter/README.md](GrayCounter/README.md) for details.