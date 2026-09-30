$ErrorActionPreference = 'Stop'

$sourceRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$runId = 'codex-reference-20260929'
$resultRoot = Join-Path $sourceRoot "results\$runId"
$artifactRoot = Join-Path $resultRoot 'artifacts'
New-Item -ItemType Directory -Force -Path $resultRoot,$artifactRoot | Out-Null

. (Join-Path $sourceRoot 'scripts\activate-idf.ps1')
$idfVersion = (& idf.py --version | Out-String).Trim()
if ($LASTEXITCODE -ne 0 -or $idfVersion -notmatch 'ESP-IDF v5\.3\.2') {
    throw "Pinned ESP-IDF 5.3.2 was not activated: $idfVersion"
}

$stamp = if ($env:CDM_BUILD_TAG) { $env:CDM_BUILD_TAG } else { Get-Date -Format 'yyyyMMdd-HHmmss' }
if ($stamp -notmatch '^[A-Za-z0-9_-]+$') { throw 'CDM_BUILD_TAG must be an ASCII directory label.' }
$stageName = "codex-desk-meter-reference-$stamp"
$stageRoot = Join-Path 'C:\Espressif\projects' $stageName
$buildRoot = Join-Path 'C:\Espressif\builds' $stageName
New-Item -ItemType Directory -Force -Path (Join-Path $stageRoot 'main'),(Join-Path $stageRoot 'managed_components') | Out-Null
Copy-Item -Recurse -Force (Join-Path $sourceRoot 'main\*') (Join-Path $stageRoot 'main')
Copy-Item -Recurse -Force (Join-Path $sourceRoot 'managed_components\*') (Join-Path $stageRoot 'managed_components')
Copy-Item -Force (Join-Path $sourceRoot 'CMakeLists.txt'),(Join-Path $sourceRoot 'sdkconfig.defaults'),(Join-Path $sourceRoot 'dependencies.lock') $stageRoot

$logPath = Join-Path $resultRoot 'build.log'
Start-Transcript -LiteralPath $logPath -Append | Out-Null
try {
    Write-Output "source_commit=$(& git -C $sourceRoot rev-parse HEAD)"
    Write-Output "source_dirty=$([bool](& git -C $sourceRoot status --porcelain))"
    Write-Output "source_workspace=$sourceRoot"
    Write-Output "ascii_stage=$stageRoot"
    Write-Output "build_dir=$buildRoot"
    Write-Output "idf_version=$idfVersion"
    if (-not (Test-Path -LiteralPath (Join-Path $stageRoot 'sdkconfig'))) {
        & idf.py -C $stageRoot -B $buildRoot set-target esp32s3
        if ($LASTEXITCODE -ne 0) { throw "idf.py set-target failed with exit code $LASTEXITCODE" }
    } else {
        Write-Output 'target_config=existing esp32s3 sdkconfig; preserving incremental build directory'
    }

    # Parallel Xtensa compilation hit an internal compiler fault in the IDF RGB driver.
    # Serial Ninja completed the same pinned toolchain build and is used for reproducibility.
    $ninjaExit = 1
    for ($attempt = 1; $attempt -le 2; $attempt++) {
        & ninja -C $buildRoot -j1 all
        $ninjaExit = $LASTEXITCODE
        if ($ninjaExit -eq 0) { break }
        if ($attempt -lt 2) { Write-Output 'ninja_retry=1 after compiler/build failure; retrying remaining work serially' }
    }
    if ($ninjaExit -ne 0) { throw "ninja -j1 all failed after retry with exit code $ninjaExit" }
    & idf.py -C $stageRoot -B $buildRoot build
    if ($LASTEXITCODE -ne 0) { throw "idf.py build failed with exit code $LASTEXITCODE" }

    $outputs = @(
        @{ Source = (Join-Path $buildRoot 'codex_desk_meter.bin'); Name = 'codex_desk_meter.bin' },
        @{ Source = (Join-Path $buildRoot 'bootloader\bootloader.bin'); Name = 'bootloader.bin' },
        @{ Source = (Join-Path $buildRoot 'partition_table\partition-table.bin'); Name = 'partition-table.bin' }
    )
    foreach ($output in $outputs) {
        if (-not (Test-Path -LiteralPath $output.Source)) { throw "Build artifact missing: $($output.Source)" }
        $destination = Join-Path $artifactRoot $output.Name
        Copy-Item -Force $output.Source $destination
        $hash = (Get-FileHash -LiteralPath $destination -Algorithm SHA256).Hash.ToLowerInvariant()
        Write-Output "artifact=$destination sha256=$hash"
    }
}
finally {
    Stop-Transcript | Out-Null
}

Write-Output "build_log=$logPath"
