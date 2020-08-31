#!/bin/bash
case x$1 in
x)
	echo Usage: $0 gitlab-api-access-token
	exit 1
	;;
x*)
	export GITLAB_ACCESS_TOKEN=$1
	;;
esac

set -e
set -x
dirname=`dirname $0`
dirname=`cd $dirname/../..; pwd`

#
# Install needed Python packages
#
python3 -m pip install -r $dirname/cwipc_test/scripts/requirements.txt

#
# Setup for using getReleaseFromGitLab
#
gRFG=$dirname/Deployment/scripts/getReleaseFromGitLab
cd $dirname
mkdir -p installed

rm -rf tmp-install
mkdir tmp-install
cd tmp-install

export CI_API_V4_URL="https://baltig.viaccess-orca.com:8443/api/v4/"
export GITLAB_ACCESS_USER_NAME="vrt_guest"
export GITLAB_ACCESS_USER_PASSWORD="VRTogether"

#
# Install releases from gitlab
#

if true; then
	python3 $gRFG --cicd --project_name cwipc_codec
	(tarfile=$PWD/cwipc_codec_osx1012*.tgz && cd /usr/local && tar -xvmf $tarfile)
fi
if true; then
	python3 $gRFG --cicd --project_name cwipc_realsense2
	(tarfile=$PWD/cwipc_realsense2_osx1012*.tgz && cd /usr/local && tar -xvmf $tarfile)
fi
if true; then
	python3 $gRFG --cicd --project_name cwipc_util
	(tarfile=$PWD/cwipc_util_osx1012*.tgz && cd /usr/local && tar -xvmf $tarfile)
fi

if false; then
	python3 $gRFG --cicd --project_name cwipc_test --release_name v2.0
	(zipfile=$PWD/loot-cwicpc.zip && cd ../installed && unzip -o $zipfile)
	(zipfile=$PWD/loot-ply.zip && cd ../installed && unzip -o $zipfile)
	#rm loot-*.zip
fi

if true; then
	python3 $gRFG --cicd --project_name SUB
	rm -rf ../signals-unity-bridge
	(tarfile=$PWD/signals-unity-bridge-*.tar.bz2 && cd .. && tar xfv $tarfile)
	(cd ../signals-unity-bridge ; ln -s [0-9]* installed)
fi

if true; then
	python3 $gRFG --cicd --project_name EncodingEncapsulation
	rm -rf ../pcl2dash
	(tarfile=$PWD/pcl2dash-*.tar.bz2 && cd .. && tar xfv $tarfile)
	(cd ../pcl2dash ; ln -s [0-9]* installed)
fi

if false; then
	python3 $gRFG --cicd --project_name DeliveryMCU
	rm -rf ../evanescent
	(tarfile=$PWD/evanescent-*.tar.bz2 && cd .. && tar xfv $tarfile)
	(cd ../evanescent ; ln -s [0-9]* installed)
	#rm evanescent-*.tar.bz2
fi
# Install symlinks for Motion Spell in users' lib directory
if true; then
	mkdir -p $HOME/lib
	cd $HOME/lib
	ln -fs $dirname/signals-unity-bridge/installed/osx/* .
	ln -fs bin2dash.dylib bin2dash.so
	ln -fs $dirname/pcl2dash/installed/osx/* .
	ln -fs signals-unity-bridge.dylib signals-unity-bridge.so
fi
