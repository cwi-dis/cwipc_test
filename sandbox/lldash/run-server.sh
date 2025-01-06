set -x
my_dir=`dirname $0`
lldash_dir=`cd $my_dir/../../../lldash/installed && pwd`
lldash_bin_dir=$lldash_dir/bin
lldash_lib_dir=$lldash_dir/lib
$lldash_bin_dir/evanescent.exe
