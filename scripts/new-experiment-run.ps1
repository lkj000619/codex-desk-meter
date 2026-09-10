[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$Provider,
    [Parameter(Mandatory = $true)]
    [string]$Product,
    [Parameter(Mandatory = $true)]
    [string]$AgentVersion,
    [Parameter(Mandatory = $true)]
    [string]$Model,
    [Parameter(Mandatory = $true)]
    [string]$Reasoning,
    [ValidateSet('cli', 'ide', 'web', 'api')]
    [string]$Interface = 'cli',
    [ValidateSet('offline-fixture', 'public-read', 'live-integration')]
    [string]$NetworkMode = 'offline-fixture',
    [string]$RunId,
    [string]$Port = '',
    [string]$HardwareSlot = 'none',
    [string]$Branch,
    [string]$Worktree = ''
)

$ErrorActionPreference = 'Stop'
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
Set-Location $repoRoot

if (-not $RunId) {
    $RunId = (Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssZ') + '-' + ($Product.ToLowerInvariant() -replace '[^a-z0-9]+', '-')
}
if ($RunId -notmatch '^[0-9]{8}T[0-9]{6}Z-[a-z0-9-]+$') {
    throw "RunId must match YYYYMMDDTHHMMSSZ-slug: $RunId"
}
if (-not $Branch) {
    $Branch = "experiment/$RunId"
}

$resultDirectory = Join-Path $repoRoot "results\$RunId"
$runDocumentDirectory = Join-Path $repoRoot "docs\agent-runs\$RunId"
if ((Test-Path -LiteralPath $resultDirectory) -or (Test-Path -LiteralPath $runDocumentDirectory)) {
    throw "Run already exists: $RunId"
}

function Get-Sha256([string]$Path) {
    return (Get-FileHash -LiteralPath (Join-Path $repoRoot $Path) -Algorithm SHA256).Hash.ToLowerInvariant()
}

function Get-FixtureSha256() {
    $lines = @(
        Get-ChildItem -LiteralPath (Join-Path $repoRoot 'experiments\fixtures') -File |
            Where-Object { $_.Name -ne 'README.md' } |
            Sort-Object FullName |
            ForEach-Object {
                $relative = $_.FullName.Substring($repoRoot.Length + 1).Replace('\', '/')
                $hash = (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
                "$hash  $relative"
            }
    )
    $canonical = ($lines -join "`n") + "`n"
    $bytes = [Text.Encoding]::UTF8.GetBytes($canonical)
    $sha256 = [Security.Cryptography.SHA256]::Create()
    try {
        $digest = $sha256.ComputeHash($bytes)
        return ([BitConverter]::ToString($digest) -replace '-', '').ToLowerInvariant()
    }
    finally {
        $sha256.Dispose()
    }
}

$baseCommit = (git rev-parse HEAD).Trim()
if ($LASTEXITCODE -ne 0 -or $baseCommit -notmatch '^[A-Fa-f0-9]{7,64}$') {
    throw 'Could not determine the current Git commit.'
}

$promptHash = Get-Sha256 'experiments/prompts/version-2-agent-task.md'
$configHash = Get-Sha256 'experiments/config/version-2-baseline.yaml'
$fixtureHash = Get-FixtureSha256
$startedAt = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ss.fffZ')

New-Item -ItemType Directory -Path $resultDirectory -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $resultDirectory 'logs') -Force | Out-Null
New-Item -ItemType Directory -Path $runDocumentDirectory -Force | Out-Null

$manifest = [ordered]@{
    schema_version = 1
    run_id = $RunId
    experiment_id = 'version-2-hardware-autonomy-v1'
    agent = [ordered]@{
        provider = $Provider
        product = $Product
        interface = $Interface
        agent_version = $AgentVersion
        model = $Model
        reasoning = $Reasoning
        configuration_sha256 = $null
    }
    execution = [ordered]@{
        started_at = $startedAt
        ended_at = $null
        timeout_seconds = 7200
        base_commit = $baseCommit
        prompt_sha256 = $promptHash
        config_sha256 = $configHash
        fixture_sha256 = $fixtureHash
        network_mode = $NetworkMode
        sandbox_policy = 'record-before-run'
        approval_policy = 'operator-approved-flash'
        branch = $Branch
        worktree = $Worktree
        host = $env:COMPUTERNAME
    }
    hardware = [ordered]@{
        board = 'waveshare-esp32-s3-lcd-3.16'
        port = if ($Port) { $Port } else { $null }
        board_revision = $null
        tf_card_present = $null
        hardware_slot = $HardwareSlot
        baseline_image_sha256 = $null
        baseline_restored = $false
    }
    measurement = [ordered]@{
        wall_clock_seconds = $null
        tool_calls = 0
        failed_commands = 0
        user_interventions = 0
        tokens = [ordered]@{
            input = $null
            output = $null
            cached = $null
            reasoning = $null
            total = $null
            availability_note = 'Fill from provider telemetry, or explain why it is unavailable.'
        }
    }
    outputs = [ordered]@{
        selection_document = "docs/agent-runs/$RunId/hardware-feature-selection.md"
        structured_result = "results/$RunId/hardware-feature.json"
        implementation_commit = $null
        build_status = 'not_run'
        automated_test_status = 'not_run'
        hardware_verification_status = 'not_run'
    }
}

$manifestPath = Join-Path $resultDirectory 'run-manifest.json'
$manifest | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $manifestPath -Encoding UTF8

$selectionPath = Join-Path $runDocumentDirectory 'hardware-feature-selection.md'
@"
# Hardware feature selection: $RunId

- Agent/product: $Product
- Interface: $Interface
- Agent version: $AgentVersion
- Model: $Model
- Reasoning: $Reasoning
- Base commit: `$baseCommit`
- Prompt SHA-256: `$promptHash`
- Config SHA-256: `$configHash`
- Fixture bundle SHA-256: `$fixtureHash`

## Candidate features

The agent must record exactly three candidates, then select one without asking the user.

## Verification notes

Fill in build, automated tests, hardware plan/result, rejected candidates, failures and risks.
"@ | Set-Content -LiteralPath $selectionPath -Encoding UTF8

Write-Host "Created run: $RunId"
Write-Host "Manifest:  $manifestPath"
Write-Host "Selection: $selectionPath"
Write-Host "Base:      $baseCommit"
Write-Host "Prompt:    $promptHash"
Write-Host "Config:    $configHash"
Write-Host "Fixtures:  $fixtureHash"
