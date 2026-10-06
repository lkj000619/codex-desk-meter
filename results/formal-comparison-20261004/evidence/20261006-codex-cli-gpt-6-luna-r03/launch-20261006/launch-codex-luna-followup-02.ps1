$ErrorActionPreference = 'Stop'
. 'C:/meter-operator-20261004/scripts/activate-idf.ps1'
Set-Location -LiteralPath 'C:/meter-operator-20261004'
& 'C:/Espressif/user-tools/python_env/idf5.3_py3.11_env/Scripts/python.exe' -B -X utf8 'C:/meter-followups-20261006/launch-codex-luna-followup-02.py'
exit $LASTEXITCODE
