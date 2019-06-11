#
# Set the following variables to where things are on your system
#
set -x
dirname=`dirname $0`
dirname=`cd $dirname/../..; pwd`
CWI_CAPTURE_FEATURE='dumpvideoframes'
pcl_render=$dirname/Installed/bin/pcl_renderer.exe

#
mkdir -p tmp-dumpedframes
cd tmp-dumpedframes
${pcl_render}
