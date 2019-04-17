#!/bin/bash
set -x
dirname=`dirname $0`
dirname=`cd $dirname/../..; pwd`
cd $dirname
instdir=`cd installed; pwd`
instdir=`cygpath -w "$instdir"`
for i in cwipc_util cwipc_realsense2 cwipc_codec ; do
(
	cd $i
	git fetch
	git pull
	(
		cd build
		cmake .. -G "Visual Studio 15 2017 Win64" -DCMAKE_INSTALL_PREFIX="$instdir" -DJPEG_Turbo_INCLUDE_DIR="C:/libjpeg-turbo64/include" -DJPEG_Turbo_LIBRARY="C:/libjpeg-turbo64/lib/jpeg.lib"
		cmake --build . --config Release
		cmake --build . --config Release --target RUN_TESTS
		cmake --build . --config Release --target INSTALL
	)	
)
done
