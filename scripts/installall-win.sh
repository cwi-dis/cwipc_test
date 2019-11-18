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
python -m pip install -r $dirname/cwipc_test/scripts/requirements.txt

#
# Setup for using getReleaseFromGitLab
#
gRFG=$dirname/Deployment/getReleaseFromGitLab
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
	python $gRFG --cicd --project_name cwipc_codec
	(zipfile=$PWD/cwipc_codec_win1064*.zip && cd .. && unzip -o $zipfile)
	#rm cwipc_codec_*.zip
fi
# Note: there is an issue with cwipc_realsense2 (or codec?) installing an older version of util.
# For now ensure we install util last.
if true; then
	python $gRFG --cicd --project_name cwipc_realsense2
	(zipfile=$PWD/cwipc_realsense2_win1064*.zip && cd .. && unzip -o $zipfile)
	#rm cwipc_realsense2_*.zip
fi
if true; then
	python $gRFG --cicd --project_name cwipc_util
	(zipfile=$PWD/cwipc_util_win1064*.zip && cd .. && unzip -o $zipfile)
	#rm cwipc_util_*.zip
fi

if false; then
	python $gRFG --cicd --project_name cwipc_test --release_name v2.0
	(zipfile=$PWD/loot-cwicpc.zip && cd ../installed && unzip -o $zipfile)
	(zipfile=$PWD/loot-ply.zip && cd ../installed && unzip -o $zipfile)
	#rm loot-*.zip
fi

if true; then
	python $gRFG --cicd --project_name SUB
	rm -rf ../signals-unity-bridge
	(tarfile=$PWD/signals-unity-bridge-*.tar.bz2 && cd .. && tar xfv $tarfile)
	(cd ../signals-unity-bridge ; ln -s [0-9]* installed)
	#rm signals-unity-bridge-*.tar.bz2
fi

if true; then
	python $gRFG --cicd --project_name EncodingEncapsulation
	rm -rf ../pcl2dash
	(tarfile=$PWD/pcl2dash-*.tar.bz2 && cd .. && tar xfv $tarfile)
	(cd ../pcl2dash ; ln -s [0-9]* installed)
	#rm pcl2dash-*.tar.bz2
fi

if false; then
	python $gRFG --cicd --project_name DeliveryMCU
	rm -rf ../evanescent
	(tarfile=$PWD/evanescent-*.tar.bz2 && cd .. && tar xfv $tarfile)
	(cd ../evanescent ; ln -s [0-9]* installed)
	#rm evanescent-*.tar.bz2
fi
