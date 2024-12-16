# Realsense Sync Tool

This project can be used to create a little USB-powered device that can be connected to the Intel RealSense D4xx sync signal.

It will display the frequency of the incoming sync signal (which should be produced by the RealSense camera that is in `MASTER` mode), in frames per second.

It can also output a "normal" Genlocked sync signal (5V, 33% duty cycle) that is in sync with the realsense signal. Optionally the realsense FPS can be divided by an integer factor (so 15FPS cameras can be synced to a 30FPS rRealsense setup).

The tool creates a WiFi Access Point, and it creates a website where the configuration can be changed.

## Construction

This project requires an ESP32-C3-0.42LCD board, which is a tiny board with an esp32c3 and a tiny LCD (as the name suggests). The board can be gotten on Banggood and such sites for a few euro (dollar, whatever), it has
a USB3 power connector and just enough I/O ports.

The board is described here: <https://github.com/01Space/ESP32-C3-0.42LCD>.



## Use

To be supplied.