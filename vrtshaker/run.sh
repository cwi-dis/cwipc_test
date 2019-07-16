#!/bin/bash
export SIGNALS_SMD_PATH=$PWD/../installed-ms/lib
export PATH="$PATH:$PWD/../evanescent/4/gnu"
export LD_LIBRARY_PATH="$PWD/../evanescent/4/gnu:$PWD/../installed-ms/signals-unity-bridge/36/gnu:$PWD/../installed-ms/pcl2dash/26/gnu"
python2 ./run.py