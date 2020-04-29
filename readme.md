# cwipc_test

Repo for pointcloud tests and other miscellaneous stuff.

## apps

There are a number of applications. All written in Python (Python 3 only), and they require all three of _cwipc\_util_, _cwipc\_realsense2_ and _cwipc\_codec_ to be installed. _PYTHONPATH_ must include `.../share/cwipc_util/python` so the programs can import the `cwipc` python module.

### Prerequisites

You need Python 3 installed, and you need to have it installed for all users. So, for windows, it should be in `C:\Python3` and not somewhere in your per-user stuff.

Then you need to install the prerequisites:

```
python3 -m pip install -r apps/requirements.txt
```

On windows you may have to use `python` in stead of `python3`.

You also need to have the directory with the Python `cwipc` module on your PYTHONPATH. The path to that directory will be something like `.../share/cwipc_util/python` depending on where you installed *cwipc_util*.

### cwipc_calibrate.py

Calibrates a number of realsense cameras. You need the "calibration cross", a device with 4 colored balls.

- Put the cross on the floor at where you want `(0, 0, 0)` to be.
- Start `cwipc_calibrate.py` (holding the cross in place) and wait for a window with a grabbed image to show up.
- You can now let go of the cross. Follow the on-screen instructions.

### cwipc\_sourceserver\_source.py

Grabs pointclouds, compresses them and sends them somewhere.

By default it creates a TCP server on port 4303. Every time a connection is opened a single pointcloud is grabbed from a realsense camera, compressed and transmitted to the client.

Using `--bin2dash` allows you to upload a dash stream of pointclouds to _evanescant_ (or another server).

When the program terminates (for example because it is killed with control-C) it prints statistics on how long grabbing, compressing and transmitting took.

The program can limit the number of pointclouds served, and it can also serve pointclouds read from file. Use `--help` for more information.

### cwipc\_sourceserver\_sink.py

Receives compressed pointclouds, decompresses them and optionally displays them. Can be used to get pointclouds from _evanescant_ or another dash server using the `--sub` option.

By default, connects to a `cwipc_sourceserver_source.py`. Every time a connection is opened a single pointcloud is received it is decompressed and optionally displayed.

By default the server should run on `localhost`, use the `--host` option to connect to a remote machine.

When the program terminates (for example because it is killed with control-C) it prints statistics on how long grabbing, compressing and transmitting took.

The program can optionally display the received pointclouds, limit the number of pointclouds requested, etc. Use `--help` for more information.

### first test

As a first test, run the following commands in two different shells/command windows:

```
python3 apps/cwipc_sourceserver_source.py --count 10
```

```
python3 apps/cwipc_sourceserver_sink.py
```

This will transmit 10 pointclouds (either grabbed from a realsense camera, or watermelons if no realsense is attached to your system) and print out the statistics.

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
