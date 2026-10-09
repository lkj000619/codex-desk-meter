$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
$zig = Join-Path $root 'firmware/.host-tools/ziglang/zig.exe'
if (-not (Test-Path -LiteralPath $zig)) {
    throw 'Install the temporary host tool: python -m pip install --no-deps --target firmware/.host-tools ziglang==0.13.0'
}
$out = Join-Path $PSScriptRoot '.build'
New-Item -ItemType Directory -Force -Path $out | Out-Null
$env:ZIG_GLOBAL_CACHE_DIR = Join-Path $root 'firmware/.host-tools/cache'
$env:ZIG_LOCAL_CACHE_DIR = $env:ZIG_GLOBAL_CACHE_DIR
& $zig cc -O0 -std=c11 -D_CRT_SECURE_NO_WARNINGS `
    "-I$(Join-Path $root 'firmware/main')" `
    '-IC:/Espressif/v5.3.2/esp-idf/components/json/cJSON' `
    (Join-Path $root 'tests/firmware/host_main.c') `
    (Join-Path $root 'firmware/main/cdm.c') `
    (Join-Path $root 'firmware/main/legacy.c') `
    'C:/Espressif/v5.3.2/esp-idf/components/json/cJSON/cJSON.c' `
    -o (Join-Path $out 'cdm-host.exe')
if ($LASTEXITCODE -ne 0) { throw "host compile failed: $LASTEXITCODE" }
