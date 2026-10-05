$ErrorActionPreference = 'Stop'
. 'C:/meter-operator-20261004/scripts/activate-idf.ps1'
Set-Location -LiteralPath 'C:/meter-operator-20261004'
& 'C:/Espressif/user-tools/python_env/idf5.3_py3.11_env/Scripts/python.exe' -B -X utf8 'C:/meter-runs-20261005/launch-codex-sol-r01.py'
exit $LASTEXITCODE
