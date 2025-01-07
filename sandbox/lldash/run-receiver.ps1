$my_path = $MyInvocation.MyCommand.Path
$my_dir = Split-Path $my_path -Parent
$cwipc_dir = $my_dir + "\..\..\..\cwipc"
$lldash_dir = $my_dir + "\..\..\..\lldash\installed"
$lldash_bin_dir = $lldash_dir + "\bin"
$Env:PATH = $lldash_bin_dir + ";" + $Env:PATH
$Env:SIGNALS_SMD_PATH = $lldash_bin_dir
& $cwipc_dir\scripts\activate.ps1
cwipc_view --sub http://localhost:9000/jacktest/bin2dashSink.mpd
