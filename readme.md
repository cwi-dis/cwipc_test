# cwipc_test

Repo for pointcloud tests.

## apps

There are two applications currently. Both written in Python (Python 3 only), and they require all three of _cwipc\_util_, _cwipc\_util_ and _cwipc\_codec_ to be installed. _PYTHONPATH_ must include `.../share/cwipc_util/python` so the programs can import the `cwipc` python module.

### Prerequisites

You need Python 3 installed, and you need to have it installed for all users. So, for windows, it should be in `C:\Python3` and not somewhere in your per-user stuff.

Then you need to install the prerequisites:

```
python3 -m pip install -r apps/requirements.txt
```

On windows you may have to use `python` in stead of `python3`.

You also need to have the directory with the Python `cwipc` module on your PYTHONPATH. The path to that directory will be something like `.../share/cwipc_util/python` depending on where you installed *cwipc_util*.

### cwipc\_sourceserver\_source.py

Creates a TCP server on port 4303. Every time a connection is opened a single pointcloud is grabbed from a realsense camera, compressed and transmitted to the client.

When the program terminates (for example because it is killed with control-C) it prints statistics on how long grabbing, compressing and transmitting took.

The program can limit the number of pointclouds served, and it can also serve pointclouds read from file. Use `--help` for more information.

### cwipc\_sourceserver\_sink.py

Connects to a `cwipc\_sourceserver\_source.py`. Every time a connection is opened a single pointcloud is received it is decompressed and optionally displayed.

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