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
$lldash_bin_dir/evanescent.exe
