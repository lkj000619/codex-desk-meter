$ErrorActionPreference = 'Stop'
. C:/meter-operator-20261004/scripts/activate-idf.ps1
# Successful Git diagnostics also use stderr; retain the native exit status.
$ErrorActionPreference = 'Continue'
& C:/Espressif/tools/python/python.exe -B -X utf8 C:/meter-operator-20261004/scripts/agy_pilot_environment.py --backup-dir C:/meter-private-preflight-20261016/argon-initial-scope --workspace C:/meter-runs-20261016/20261016-antigravity-cli-agy-argon-high-r01/checkout run -- C:/Espressif/tools/python/python.exe -B -X utf8 C:/meter-operator-20261004/scripts/benchmark.py run C:/meter-runs-20261016/20261016-antigravity-cli-agy-argon-high-r01 --receipt C:/meter-preflight-20261016/argon-high/launch-evidence/receipt.json
exit $LASTEXITCODE
