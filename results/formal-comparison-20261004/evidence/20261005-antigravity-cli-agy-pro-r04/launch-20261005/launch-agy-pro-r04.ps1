$ErrorActionPreference = 'Stop'
. 'C:/meter-operator-20261004/scripts/activate-idf.ps1'
$env:AGY_CLI_DISABLE_AUTO_UPDATE = 'true'
Set-Location -LiteralPath 'C:/meter-operator-20261004'
& 'C:/Espressif/user-tools/python_env/idf5.3_py3.11_env/Scripts/python.exe' -B -X utf8 'C:/meter-followups-20261005/launch-agy-pro-r04.py'
exit $LASTEXITCODE
