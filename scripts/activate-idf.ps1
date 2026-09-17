param(
    [string]$InstallRoot = 'C:\Espressif',
    [string]$IdfVersion = '5.3.2',
    [string]$ToolsRoot = ''
)

$ErrorActionPreference = 'Stop'

$profilePath = Join-Path $InstallRoot "tools\Microsoft.v$IdfVersion.PowerShell_profile.ps1"
$asciiTempPath = Join-Path $InstallRoot 'tmp'

if (-not (Test-Path -LiteralPath $asciiTempPath)) {
    New-Item -ItemType Directory -Path $asciiTempPath | Out-Null
}

# ESP-IDF v5.3.2의 Windows 도구 일부는 한글 경로에서 실패할 수 있다.
$env:TEMP = $asciiTempPath
$env:TMP = $asciiTempPath
$env:PYTHONUTF8 = '1'
$env:PYTHONIOENCODING = 'utf-8'

if (-not $ToolsRoot) {
    $repairedTools = Join-Path $InstallRoot 'user-tools'
    if (Test-Path -LiteralPath $repairedTools) { $ToolsRoot = $repairedTools }
}

if ($ToolsRoot) {
    # Use the repaired ASCII tool installation without evaluating the broken EIM profile.
    $env:IDF_PATH = Join-Path $InstallRoot "v$IdfVersion\esp-idf"
    $env:IDF_TOOLS_PATH = (Resolve-Path -LiteralPath $ToolsRoot).Path
    $idfToolsScript = Join-Path $env:IDF_PATH 'tools\idf_tools.py'
    if (-not (Test-Path -LiteralPath $idfToolsScript)) {
        throw "ESP-IDF tools script not found: $idfToolsScript"
    }
    $majorMinor = ($IdfVersion -split '\.')[0..1] -join '.'
    $pythonEnvs = @(Get-ChildItem -LiteralPath (Join-Path $ToolsRoot 'python_env') -Directory |
        Where-Object { $_.Name -like "idf${majorMinor}_py*_env" })
    if ($pythonEnvs.Count -ne 1) {
        throw "Expected one Python environment for IDF $majorMinor under $ToolsRoot/python_env."
    }
    $env:IDF_PYTHON_ENV_PATH = $pythonEnvs[0].FullName
    $pythonScripts = Join-Path $env:IDF_PYTHON_ENV_PATH 'Scripts'
    $idfPython = Join-Path $pythonScripts 'python.exe'
    if (-not (Test-Path -LiteralPath $idfPython)) { throw "Python not found: $idfPython" }
    $env:PATH = "$pythonScripts;$env:PATH"
    $exportLines = & $idfPython $idfToolsScript export --format key-value
    if ($LASTEXITCODE -ne 0) { throw 'ESP-IDF tool export failed.' }
    foreach ($line in $exportLines) {
        $pair = $line -split '=', 2
        if ($pair.Count -ne 2 -or $pair[0] -notmatch '^[A-Z_][A-Z0-9_]*$') {
            throw "Unexpected ESP-IDF export line: $line"
        }
        if ($pair[0] -eq 'PATH') {
            $env:PATH = $pair[1].Replace('%PATH%', $env:PATH)
        }
        else { Set-Item -LiteralPath "Env:$($pair[0])" -Value $pair[1] }
    }
    function global:idf.py { & (Join-Path $env:IDF_PYTHON_ENV_PATH 'Scripts\python.exe') (Join-Path $env:IDF_PATH 'tools\idf.py') @args }
    & $idfPython $idfToolsScript check-python-dependencies
    if ($LASTEXITCODE -ne 0) { throw 'ESP-IDF Python dependencies failed validation.' }
}
else {
    if (-not (Test-Path -LiteralPath $profilePath)) {
        throw "ESP-IDF activation profile was not found: $profilePath"
    }
    . $profilePath
}

# EIM 기본 프로필은 ccache를 활성화하지만, 한글 사용자 경로에서 ccache 4.10.2가
# 문자 변환 오류를 일으킨다. 현재 기준 환경에서는 재현성을 위해 비활성화한다.
$env:IDF_CCACHE_ENABLE = '0'

$actualIdfVersion = idf.py --version
if ($LASTEXITCODE -ne 0 -or ($actualIdfVersion -join "`n") -notmatch "ESP-IDF v$([regex]::Escape($IdfVersion))(?:\s|$)") {
    throw "ESP-IDF version check failed: $actualIdfVersion"
}

Write-Host ''
Write-Host "Codex Desk Meter ESP-IDF environment is ready (ESP-IDF $IdfVersion)."
Write-Host 'Use an ASCII-only project alias or clone path when running idf.py.'
