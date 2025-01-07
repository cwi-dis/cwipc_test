$my_path = $MyInvocation.MyCommand.Path
$my_dir = Split-Path $my_path -Parent
$lldash_dir = $my_dir + "\..\..\..\lldash\installed"
$lldash_bin_dir = $lldash_dir + "\bin"
$Env:PATH = $lldash_bin_dir + ";" + $Env:PATH
$Env:SIGNALS_SMD_PATH = $lldash_bin_dir
& $lldash_bin_dir\evanescent.exe
