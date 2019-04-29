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
	python $gRFG --cicd --project_name cwipc_util
	(zipfile=$PWD/cwipc_util_win1064*.zip && cd .. && unzip -o $zipfile)
	rm cwipc_util_*.zip
fi

if true; then
	python $gRFG --cicd --project_name cwipc_realsense2
	(zipfile=$PWD/cwipc_realsense2_win1064*.zip && cd .. && unzip -o $zipfile)
	rm cwipc_realsense2_*.zip
fi

if true; then
	python $gRFG --cicd --project_name cwipc_codec
	(zipfile=$PWD/cwipc_codec_win1064*.zip && cd .. && unzip -o $zipfile)
	rm cwipc_codec_*.zip
fi

if true; then
	python $gRFG --cicd --project_name cwipc_test --release_name v1.1
	(zipfile=$PWD/loot-cwicpc.zip && cd ../installed && unzip -o $zipfile)
	(zipfile=$PWD/loot-ply.zip && cd ../installed && unzip -o $zipfile)
	rm loot-*.zip
fi

if true; then
	python $gRFG --cicd --project_name SUB
	rm -rf ../signals-unity-bridge
	mkdir -p ../signals-unity-bridge
	(zipfile=$PWD/v*_stable.zip && cd ../signals-unity-bridge && unzip -o $zipfile)
fi

if true; then
	python $gRFG --cicd --project_name EncodingEncapsulation --release_name "Release v19 (Win10 64 bits)"
	rm -rf ../pcl2dash
	mkdir -p ../pcl2dash
	(zipfile=$PWD/EncodingEncapsulation_Win10*.zip && cd ../pcl2dash && unzip -o $zipfile)
	rm EncodingEncapsulation*.zip
fi
