#
# Set the following variables to where things are on your system
#
set -x
dirname=`dirname $0`
dirname=`cd $dirname/../..; pwd`
gpac_dash_server=$dirname/node-gpac-dash/gpac-dash.js
pcl2dash=$dirname/pcl2dash/v19/x64/Release/pcl2dash.exe
#
mkdir -p tmp-dash
cd tmp-dash
node ${gpac_dash_server} -segment-marker eods -chunk-media-segments &
nodepid=$!
${pcl2dash} -t 1 -n -1 -s 1000
kill $nodepid
