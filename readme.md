# cwipc_test

Repo for pointcloud tests and other miscellaneous stuff.

## VRTShaker (DASH transmission test)

The VRTShaker is intended for testing the latency of the DASH transmission chain. VRTShaker is made of 2 small C programs using the C API of bin2dash and the SUB. Instead of real data these programs read and write capture times.

You need to have the binaries from EncodingEncapsulation (bin2dash.so), the Signals Unity Bridge (SUB), and the SFU (Evanescent) installed on your system. Please customize build.sh and run.sh with your location to these tools.

The ```run.py``` script launches all the setup to transmit data. It outputs a verbose text containing the latency in this form:

```
Latency: 0.02 s
Latency: 0.01 s
Latency: 0.01 s
...

```

## loot datasets

To create the loot datasets for testing:

- Download the original dataset from <https://jpeg.org/plenodb/pc/8ilabs/> into `../loot`.
	
	- You may have to edit the `Makefile` to show it where the dataset is.
- Install _cwipc\_util_ and _cwipc\_codec_.
- Clone the Deployment repo <https://baltig.viaccess-orca.com:8443/VRT/deployment-group/Deployment> into `../Deployment`.
	
	- Again, you may have to edit the `Makefile` if pathnames are different.
- Check that the _cwipc_ stuff is installed correctly and install dependencies (_numpy_, _open3d_):

  ```
  make deps
  ```
- Convert loot to smaller pointclouds, and compress those to _cwicpc_ files:

  ```
  make
  ```
 - Upload, possibly after editing `config/addReleaseToGitLab.json`:

   ```
   make release
   ```

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
