#!/bin/bash
set -x
dirname=`dirname $0`
dirname=`cd $dirname/../..; pwd`
cd $dirname
for i in cwipc_util cwipc_realsense2 cwipc_codec ; do
(
	cd $i
	git fetch
	git checkout master
	git pull
	rm -rf build
	mkdir build
)
done
