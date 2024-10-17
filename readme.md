# cwipc_test

Repo for pointcloud tests and other miscellaneous stuff.

## Samples

Various sets of compressed and uncompressed point cloud sequences. See [Samples/readme.md](Samples/readme.md).

## doc

Historical significance: documentation of the VRTogether pipeline.

## pointcloud-color-test

Documents for testing point cloud capture color matching.

## pointcloud-registration-test

Documents for testing point cloud registration.


## Helper scripts

## Installing developer dependencies

There is a script `checkinstall-win.sh` that tries to check whether all VRtogether modules and all third-party dependencies have been
installed and are on PATH correctly.

There is a script `installall-win.sh` that will try to install all VRtogether releases.

Installing the third party dependencies has to be done manually. Currently the information on what to install is scattered around the various *README* files of all the modules.

### Building everything from source

The are scripts `buildall.sh`, `cleanall.sh` and `buildall-win.sh` which build and clean checked out copies of the cwipc_* modules, but probably only if your layout is the same as for Jack.

## Doc

Some documents by Jack on the architecture (because he can't get his head around Google Docs for anything but the simplest word processing and spreadsheet documents).

- [Component Architecture](doc/component-architecture.md)

## Sync testing

The arduino program in _neopixelsync_ should be built and flashed onto an Arduino Nano. Attach a strip of 18 neopixels (pin 6 is the data connection). Connect to USB power supply. The first two pixels will light up red and orangeish, the third pixel will be off. The rest will be a strip of green ones, with each next pixel lit up 3ms after the previous one.

The script in `synch-scripts/dumpframes.sh` will capture 10 pointclouds from all attached cameras, and in addition it will dump the PNG images from the RGB data. Point all cameras at the led strip. Compare the corresponding images to see whether the cameras are in sync.

## sandbox

Random junk that may be useful.
