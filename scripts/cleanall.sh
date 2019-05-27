#!/bin/bash
set -x
dirname=`dirname $0`
dirname=`cd $dirname/../..; pwd`
case x$1 in
x) branchname=master ;;
*) branchname=$1 ;;
esac
cd $dirname
for i in cwipc_util cwipc_realsense2 cwipc_codec ; do
if [ -d $i ]; then
(
	cd $i
	git fetch
	git checkout $branchname
	git pull
	rm -rf build
	mkdir build
)
fi
done
