#!/bin/bash
export CI_PROJECT_NAME=Deployment
export GITLAB_ACCESS_TOKEN="5NpQ2psr2D2jnjpeWGy7"
export CI_COMMIT_TAG=issue57-test-jack
export CI_BUILD_TAG=issue57-test-jack
export CI_COMMIT_MESSAGE="testing issue57"
export CI_API_V4_URL=https://baltig.viaccess-orca.com:8443/api/v4/
./Deployment/scripts/deployment-build-installer.sh  --cicd --verbose --noupload --no3rdparty $GITLAB_ACCESS_TOKEN
