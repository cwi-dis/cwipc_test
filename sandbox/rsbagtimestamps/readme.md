# Check realsense recording timestamps

This script allows you to test Realsense recordings (bag files) for dropped frames and timing consistency.

It will read the bag files and produce a spreadsheet with the timing information of the captured and recorded frames. This allows you to manually inspect what has been recorded, and whether there are any missing frames.

## Usage

Mac/Linux bash:

```
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
cd directory-with-bagfiles
python path/to/rsbagtimestamps.py *.bag
```

Windows CMD:

```
python -m venv .venv
.venv\Scripts\activate.bat
pip install -r requirements.txt
cd directory-with-bagfiles
python path/to/rsbagtimestamps.py *.bag
```

> Hmm it seems wildcards don't work on Windows. Specify all bag files by hand.

This will create a file `ts-12345678.bag.csv` for every `12345678.bag` containing all the timestamps. Open these files in Excel or some other spreadsheet. The last two columns, `d_dur` and `rgb_dur`, are easiest to inspect: these are the dureaction of the depth and color frame just captured. After some initial startup these should be consistent.

## Synchronization checking

This does not work yet.

```
python -m .../rsbagtimestamps.py --concurrent *.bag > concurrent.csv
```



