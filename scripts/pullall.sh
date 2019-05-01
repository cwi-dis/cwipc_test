#!/bin/bash
set -x
dirname=`dirname $0`
dirname=`cd $dirname/../..; pwd`
cd $dirname
for i in */.git ; do
(
	cd $i/..
	git fetch
	git pull
)
done
