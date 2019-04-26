#
# Set the following variables to where things are on your system
#
set -x
dirname=`dirname $0`
dirname=`cd $dirname/../..; pwd`
gpac_dash_server=$dirname/node-gpac-dash/gpac-dash.js
bin2dash=$dirname/pcl2dash/v19/x64/Release/bin2dash_app.exe
lootcompressed=$dirname/installed/lootCwicpc
#
rm -rf tmp-dash
mkdir tmp-dash
cd tmp-dash
node ${gpac_dash_server} -segment-marker eods -chunk-media-segments &
nodepid=$!
${bin2dash} -s 33 $lootcompressed
kill $nodepid
