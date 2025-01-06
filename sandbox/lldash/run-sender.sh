set -x
my_dir=`dirname $0`
lldash_dir=`cd $my_dir/../../../lldash/installed && pwd`
lldash_bin_dir=$lldash_dir/bin
lldash_lib_dir=$lldash_dir/lib
# source $my_dir/../../../cwipc/scripts/activate
export SIGNALS_SMD_PATH=$lldash_lib_dir
cwipc_forward --synthetic --nodrop --bin2dash http://localhost:9000/jacktest/
