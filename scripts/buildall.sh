#!/bin/bash
set -x
set -e
dirname=`dirname $0`
dirname=`cd $dirname/../..; pwd`
cd $dirname
for i in cwipc_util cwipc_realsense2 cwipc_codec ; do
(
	cd $i
	git fetch
	git pull
	(
		cd build
		cmake ..
		make
		make test
		make install
	)	
)
done
