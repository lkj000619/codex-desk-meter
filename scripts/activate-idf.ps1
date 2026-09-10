param(
    [string]$InstallRoot = 'C:\Espressif',
    [string]$IdfVersion = '5.3.2'
)

$ErrorActionPreference = 'Stop'

$profilePath = Join-Path $InstallRoot "tools\Microsoft.v$IdfVersion.PowerShell_profile.ps1"
$asciiTempPath = Join-Path $InstallRoot 'tmp'

if (-not (Test-Path -LiteralPath $profilePath)) {
    throw "ESP-IDF activation profile was not found: $profilePath"
}

if (-not (Test-Path -LiteralPath $asciiTempPath)) {
    New-Item -ItemType Directory -Path $asciiTempPath | Out-Null
}

# ESP-IDF v5.3.2의 Windows 도구 일부는 한글 경로에서 실패할 수 있다.
$env:TEMP = $asciiTempPath
$env:TMP = $asciiTempPath
$env:PYTHONUTF8 = '1'
$env:PYTHONIOENCODING = 'utf-8'

. $profilePath

# EIM 기본 프로필은 ccache를 활성화하지만, 한글 사용자 경로에서 ccache 4.10.2가
# 문자 변환 오류를 일으킨다. 현재 기준 환경에서는 재현성을 위해 비활성화한다.
$env:IDF_CCACHE_ENABLE = '0'

Write-Host ''
Write-Host "Codex Desk Meter ESP-IDF environment is ready (ESP-IDF $IdfVersion)."
Write-Host 'Use an ASCII-only project alias or clone path when running idf.py.'
