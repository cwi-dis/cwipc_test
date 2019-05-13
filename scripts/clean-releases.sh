#!/bin/bash
case x$2 in
x)
	echo Usage: $0 gitlab-api-access-token projectname releasename
	exit 1
	;;
x*)
	export GITLAB_ACCESS_TOKEN=$1
	projectname=$2
	releasename=$3
	;;
esac

set -e
set -x
dirname=`dirname $0`
dirname=`cd $dirname/../..; pwd`

#
# Setup for using getReleaseFromGitLab
#
gRFG=$dirname/Deployment/getReleaseFromGitLab
aRTG=$dirname/Deployment/addReleaseToGitLab
export CI_API_V4_URL="https://baltig.viaccess-orca.com:8443/api/v4/"
export GITLAB_ACCESS_USER_NAME="vrt_guest"
export GITLAB_ACCESS_USER_PASSWORD="VRTogether"

case x$3 in
x)
	python3 $gRFG --cicd --project_name $projectname --listreleases
	;;
x*)
	python3 $aRTG --cicd --project_name $projectname --tag_name $releasename --deleterelease
	;;
esac