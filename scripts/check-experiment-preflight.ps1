[CmdletBinding()]
param(
    [string]$Port = 'COM3',
    [switch]$RequireHardware,
    [switch]$SkipIdf
)

$ErrorActionPreference = 'Stop'
$script:Failures = 0
$script:Warnings = 0
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path

function Check-Ok([string]$Message) {
    Write-Host "[OK]   $Message" -ForegroundColor Green
}

function Check-Warn([string]$Message) {
    $script:Warnings++
    Write-Host "[WARN] $Message" -ForegroundColor Yellow
}

function Check-Fail([string]$Message) {
    $script:Failures++
    Write-Host "[FAIL] $Message" -ForegroundColor Red
}

Set-Location $repoRoot

if (-not (Test-Path -LiteralPath (Join-Path $repoRoot '.git'))) {
    Check-Fail "Git repository not found: $repoRoot"
}
else {
    Check-Ok "Git repository: $repoRoot"
}

$requiredFiles = @(
    'README.md',
    'docs/PROJECT_PURPOSE.md',
    'docs/PRODUCT_CONTRACT.md',
    'docs/DEVELOPMENT_ENVIRONMENT.md',
    'docs/experiments/agent-experiment-protocol.md',
    'experiments/config/version-2-baseline.yaml',
    'experiments/prompts/version-2-agent-task.md',
    'experiments/schema/run-manifest.schema.json',
    'experiments/schema/hardware-feature-result.schema.json',
    'scripts/validate-experiment-result.py',
    'scripts/new-experiment-run.ps1'
)
foreach ($relativePath in $requiredFiles) {
    if (Test-Path -LiteralPath (Join-Path $repoRoot $relativePath)) {
        Check-Ok "Required file: $relativePath"
    }
    else {
        Check-Fail "Missing required file: $relativePath"
    }
}

$idfReady = $false
if (-not $SkipIdf) {
    $activate = Join-Path $PSScriptRoot 'activate-idf.ps1'
    if (Test-Path -LiteralPath $activate) {
        try {
            . $activate
            $idf = Get-Command idf.py -ErrorAction Stop
            $idfVersion = (& $idf --version | Select-Object -First 1)
            if ($idfVersion -match 'ESP-IDF v5\.3\.2') {
                Check-Ok "ESP-IDF pinned: $idfVersion"
                $idfReady = $true
            }
            else {
                Check-Warn "ESP-IDF found but version is not v5.3.2: $idfVersion"
            }
        }
        catch {
            Check-Warn "ESP-IDF is not available in this shell: $($_.Exception.Message)"
        }
    }
}

$readmeBytes = [System.IO.File]::ReadAllBytes((Join-Path $repoRoot 'README.md'))
$isUtf16 = $readmeBytes.Length -ge 2 -and (($readmeBytes[0] -eq 0xFF -and $readmeBytes[1] -eq 0xFE) -or ($readmeBytes[0] -eq 0xFE -and $readmeBytes[1] -eq 0xFF))
if ($isUtf16) {
    Check-Fail 'README.md is UTF-16; commit UTF-8 text instead.'
}
else {
    Check-Ok 'README.md is not UTF-16 binary text'
}

$validator = Join-Path $repoRoot 'scripts/validate-experiment-result.py'
$python = Get-Command python -ErrorAction SilentlyContinue
if ($null -eq $python -and -not $idfReady) {
    $python = Get-Command py -ErrorAction SilentlyContinue
}
if ($null -eq $python) {
    Check-Fail 'python was not found on PATH'
}
else {
    if ($python.Name -eq 'py.exe') {
        & $python.Source '-3' $validator
    }
    else {
        & $python.Source $validator
    }
    if ($LASTEXITCODE -eq 0) {
        Check-Ok 'Example manifest/result validation'
    }
    else {
        Check-Fail 'Example manifest/result validation'
    }
}

$serial = Get-CimInstance Win32_SerialPort -ErrorAction SilentlyContinue | Where-Object { $_.DeviceID -eq $Port }
if ($null -ne $serial) {
    Check-Ok "Hardware port present: $Port ($($serial.Status))"
}
elseif ($RequireHardware) {
    Check-Fail "Required hardware port not found: $Port"
}
else {
    Check-Warn "Hardware port not found: $Port (use -RequireHardware for a hard failure)"
}

$gitStatus = @(git status --porcelain)
if ($gitStatus.Count -eq 0) {
    Check-Ok 'Working tree is clean'
}
else {
    Check-Warn "Working tree has $($gitStatus.Count) change(s); commit before baseline tagging"
}

Write-Host ''
Write-Host "Preflight summary: $script:Failures failure(s), $script:Warnings warning(s)."
if ($script:Failures -gt 0) {
    exit 1
}
exit 0
