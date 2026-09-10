param(
    [string]$VendorRoot = 'C:\Espressif\vendor\waveshare-esp32-s3-lcd-3.16',
    [switch]$Redownload
)

$ErrorActionPreference = 'Stop'

$downloadUrl = 'https://files.waveshare.com/wiki/ESP32-S3-LCD-3.16/ESP32-S3-LCD-3.16-Demo.zip'
$zipPath = Join-Path $VendorRoot 'ESP32-S3-LCD-3.16-Demo.zip'
$sourceRoot = Join-Path $VendorRoot 'source'
$demoRoot = Join-Path $sourceRoot 'ESP32-S3-LCD-3.16-Demo'
$idfRoot = Join-Path $demoRoot 'ESP-IDF'

if (-not (Test-Path -LiteralPath $VendorRoot)) {
    New-Item -ItemType Directory -Path $VendorRoot -Force | Out-Null
}

if ($Redownload -or -not (Test-Path -LiteralPath $zipPath)) {
    Write-Host "Downloading $downloadUrl"
    Invoke-WebRequest -Uri $downloadUrl -OutFile $zipPath -UseBasicParsing
}

$hash = (Get-FileHash -LiteralPath $zipPath -Algorithm SHA256).Hash
Write-Host "Demo ZIP: $zipPath"
Write-Host "SHA256:   $hash"

if (-not (Test-Path -LiteralPath $idfRoot)) {
    if (-not (Test-Path -LiteralPath $sourceRoot)) {
        New-Item -ItemType Directory -Path $sourceRoot -Force | Out-Null
    }

    # The package contains large Arduino assets too; extract only the ESP-IDF tree.
    tar -xf $zipPath -C $sourceRoot 'ESP32-S3-LCD-3.16-Demo/ESP-IDF/*'
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to extract ESP-IDF examples from $zipPath"
    }
}

if (-not (Test-Path -LiteralPath $idfRoot)) {
    throw "ESP-IDF examples were not found after extraction: $idfRoot"
}

Write-Host "ESP-IDF examples: $idfRoot"
Get-ChildItem -LiteralPath $idfRoot -Directory | Sort-Object Name | Select-Object -ExpandProperty Name
