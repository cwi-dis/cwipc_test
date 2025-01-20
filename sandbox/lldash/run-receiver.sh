set -e
case x$1 in
  x)
    echo Usage: $0 lldash-dir
    echo lldash-dir is toplevel directory of lldash installation
    exit 1
    ;;
  x*)
    lldash_dir=`realpath $1`
    ;;
esac
set -x
lldash_bin_dir=$lldash_dir/bin
lldash_lib_dir=$lldash_dir/lib
# source $my_dir/../../../cwipc/scripts/activate
export SIGNALS_SMD_PATH=$lldash_lib_dir
case `uname -s` in
Linux)
    export LD_LIBRARY_PATH=$SIGNALS_SMD_PATH:$LD_LIBRARY_PATH
    ;;
esac
cwipc_view --sub http://localhost:9000/jacktest/bin2dashSink.mpd
