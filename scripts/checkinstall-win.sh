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
# Check third party packages
#

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

