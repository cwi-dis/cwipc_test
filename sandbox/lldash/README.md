# MotionSpell/CWI LLDASH test scripts

Some initial script to test whether the new lldash works.

Scripts are available for bash (Linux, Mac) or PowerShell (Windows).

## Usage (Mac, Linux)

- Ensure you have a recent `cwipc` on your path (possibly by building it and running `source .../cwipc/scripts/activate` in this shell
- Download an lldash distribution tarball for your system and unpack it.
- Run `./run-server.sh lldash-dir` in one window
- Run `./run-sender.sh lldash-dir` in another window
- Wait for the first mpd file to have ben uploaded
- Run `./run-receiver.sh lldash-dir` in a third window


## Usage (Windows)

- Ensure you have a recent `cwipc` on your path (possibly by building it and running `source .../cwipc/scripts/activate` in this shell
- Download an lldash distribution tarball for your system and unpack it in `../../../lldash-installed`
- Run `& run-server.ps1` in one window
- Run `& run-sender.ps1` in a second window
- Wait for the first mpd file to have ben uploaded
- Run `& run-receiver.ps1` in a third window
