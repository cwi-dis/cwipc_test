#!/bin/bash
set -x
echo "Make sure the stroboscope is on. Grabbing RGB images along with pointclouds."
rm -rf tmp-synctest
mkdir tmp-synctest
cd tmp-synctest
export CWI_CAPTURE_FEATURE=dumpvideoframes
cwipc_grab 10 .
echo "Please check PNG images in $PWD for correspondence"
