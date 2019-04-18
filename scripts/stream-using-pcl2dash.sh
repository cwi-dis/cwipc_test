#
# Set the following variables to where things are on your system
#
gpac_dash_server=/c/Users/dis/jack/src/VRtogether/node-gpac-dash/gpac-dash.js
pcl2dash=/c/Users/dis/jack/src/VRtogether/pcl2dash/v18/x64/Release/pcl2dash.exe
#
rm -rf tmp-dash
mkdir tmp-dash
cd tmp-dash
node ${gpac_dash_server} -segment-marker eods -chunk-media-segments &
nodepid=$!
${pcl2dash} -t 1 -n -1 -s 1000
kill $nodepid