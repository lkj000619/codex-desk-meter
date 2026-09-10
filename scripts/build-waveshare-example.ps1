param(
    [ValidateSet('factory', 'lvgl9')]
    [string]$Example = 'factory',
    [string]$VendorRoot = 'C:\Espressif\vendor\waveshare-esp32-s3-lcd-3.16',
    [string]$IdfVersion = '5.3.2'
)

$ErrorActionPreference = 'Stop'

$idfRoot = Join-Path $VendorRoot 'source\ESP32-S3-LCD-3.16-Demo\ESP-IDF'
$exampleDirectory = if ($Example -eq 'factory') { '09_FactoryProgram' } else { '08_LVGL_V9_Test' }
$projectPath = Join-Path $idfRoot $exampleDirectory
$buildPath = Join-Path $VendorRoot "build\$exampleDirectory-v$IdfVersion"

if (-not (Test-Path -LiteralPath $projectPath)) {
    throw "Waveshare example not found. Run fetch-waveshare-demo.ps1 first: $projectPath"
}

. (Join-Path $PSScriptRoot 'activate-idf.ps1') -IdfVersion $IdfVersion

Write-Host "Building $exampleDirectory with ESP-IDF $IdfVersion"
Write-Host "Project: $projectPath"
Write-Host "Build:   $buildPath"

idf.py -C $projectPath -B $buildPath build
if ($LASTEXITCODE -ne 0) {
    throw "ESP-IDF build failed for $exampleDirectory (exit code $LASTEXITCODE)"
}

Write-Host ''
Write-Host 'Build succeeded. No flash or monitor action was requested.'
