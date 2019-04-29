#!/bin/bash
case x$1 in
x)
	error_occurred() {
		exit 1
	}
	;;
x--continue)
	error_occurred() {
		true
	}

	;;
esac

dirname=`dirname $0`
dirname=`cd $dirname/../..; pwd`
rm -rf $dirname/tmp-check-install
mkdir $dirname/tmp-check-install
cd $dirname/tmp-check-install
#
# Check repos
#
if [ ! -d $dirname/cwipc_test/scripts ] ; then
	echo cwipc_test: gitlab repository not checked out, should be in $dirname
	error_occurred
else
	echo cwipc_test: ok
fi

if [ ! -f $dirname/Deployment/getReleaseFromGitlab ]; then
	echo Deployment: gitlab repository not checked out, should be in $dirname
	error_occurred
else
	echo Deployment: ok
fi

#
# Check Python and Python version
#
pyver=`python --version 2>&1`
if [ $? -ne 0 ]; then
	echo python: not installed, or not on PATH
	error_occurred
else
	case $pyver in
	'Python 3'*)
		echo python: ok
		;;
	*)
		echo python: incorrect version, must be Python3
		error_occurred
	esac
fi
#
# Check node
#
nodever=`node --version 2>&1`
if [ $? -ne 0 ]; then
	echo node: not installed, or not on PATH
	error_occurred
else
	echo node: ok
fi
#
# Check third party packages
#
if [ ! -f $dirname/node-gpac-dash/gpac-dash.js ]; then
	echo node-gpac-dash: github repository not checked out, should be in $dirname
	error_occurred
else
	echo node-gpac-dash: ok
fi

jpegver=`cjpeg -version > /dev/null 2>&1`
if [ $? -ne 0 ]; then
	echo jpeg-turbo: not installed, or not on PATH
	error_occurred
else
	echo jpeg-turbo: ok
fi

python -c "import ctypes ; ctypes.CDLL('realsense2.dll')"
if [ $? -ne 0 ]; then
	echo realsense2: not installed or not on PATH
	error_occurred
else
	echo realsense2: ok
fi

pcl_ply2ply_release --version > /dev/null
if [ $? -ne 0 ]; then
	echo pcl: not installed, or not on PATH
	error_occurred
else
	echo pcl: ok
fi

#
# Check VRtogether releases
#
cwipc_generate 1 .
if [ $? -ne 0 ]; then
	echo cwipc_util: not installed, or not on PATH, or problem with dependency
	error_occurred
else
	echo cwipc_util: ok
fi

cwipc_grab 1 .
if [ $? -ne 0 ]; then
	echo cwipc_realsense2: not installed, or not on PATH, or problem with dependency
	error_occurred
else
	echo cwipc_realsense2: ok
fi

cwipc_generate 1 .
if [ $? -ne 0 ]; then
	echo cwipc_codec: not installed, or not on PATH, or problem with dependency
	error_occurred
else
	echo cwipc_codec: ok
fi

pcl2dash=$dirname/pcl2dash/v19/x64/Release/pcl2dash.exe
$pcl2dash --version > /dev/null 2>&1
if [ $? -ne 1 ]; then
	echo pcl2dash: not installed, or not on PATH, or problem with dependency
	error_occurred
else
	echo pcl2dash: ok
fi

python -c "import ctypes ; ctypes.CDLL('signals-unity-bridge.dll')"
if [ $? -ne 0 ]; then
	echo signals-unity-bridge: not installed, or not on PATH, or problem with dependency
	error_occurred
else
	echo signals-unity-bridge: ok
fi

if [ ! -f $dirname/installed/lootCwicpc/loot_vox10_1299.cwicpc ]; then
	echo lootCwicpc: not installed, should be in  $dirname/installed/lootCwicpc
	error_occurred
else
	echo lootCwicpc: ok
fi

