param([switch]$VerifyOnly)
$ErrorActionPreference = 'Stop'
$taskRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$taskEncoding = New-Object Text.UTF8Encoding($false)
$taskContextPath = Join-Path $taskRoot 'experiments/orca-harness-20261008/context.json'
$taskContext = [IO.File]::ReadAllText($taskContextPath, $taskEncoding) | ConvertFrom-Json
$taskBranch = git -C $taskRoot branch --show-current
if ($LASTEXITCODE -ne 0 -or $taskBranch.Trim() -ne $taskContext.branch) { throw 'Wrong branch; prior snapshot retained.' }
$taskManifestPath = Join-Path $taskRoot 'experiments/orca-harness-20261008/frozen-inputs.json'
$taskManifest = [IO.File]::ReadAllText($taskManifestPath, $taskEncoding) | ConvertFrom-Json
foreach ($taskInput in $taskManifest.files) {
    $taskPath = [IO.Path]::GetFullPath((Join-Path $taskRoot $taskInput.path))
    if (-not $taskPath.StartsWith($taskRoot + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) {
        throw "Input path escapes checkout: $($taskInput.path)"
    }
    $taskActualHash = (Get-FileHash -LiteralPath $taskPath -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($taskActualHash -ne $taskInput.sha256) { throw "Frozen input changed: $($taskInput.path)" }
}
if ($taskManifest.files.Count -ne 57) { throw 'Expected 57 preserved inputs' }
if ($VerifyOnly) { Write-Output '57 frozen input hashes verified; context and manifest parsed.'; return }

$taskListReceipt = orca orchestration task-list --run $taskContext.run_id --json | ConvertFrom-Json
if ($LASTEXITCODE -ne 0 -or -not $taskListReceipt.ok) { throw 'Orca task snapshot failed; prior snapshot retained.' }
$taskFleetReceipt = orca orchestration worker-list --run $taskContext.run_id --include-remote --json | ConvertFrom-Json
if ($LASTEXITCODE -ne 0 -or -not $taskFleetReceipt.ok) { throw 'Orca worker snapshot failed; prior snapshot retained.' }
$taskSnapshot = [ordered]@{
    observed_at = [DateTime]::UtcNow.ToString('o')
    run_id = $taskContext.run_id
    frozen_inputs_verified = 57
    snapshot_kind = 'read-only-native-runtime-observation-not-completion-authority'
    tasks = @($taskListReceipt.result.tasks | ForEach-Object {
        [ordered]@{ id=$_.id; title=$_.task_title; status=$_.status; deps=$_.deps; completed_at=$_.completed_at }
    })
    workers = @($taskFleetReceipt.result.workers | ForEach-Object {
        [ordered]@{
            task_id=$_.taskId; dispatch_id=$_.dispatchId; terminal_handle=$_.agentTerminalHandle
            state=$_.workerState; dispatch_status=$_.dispatchStatus
            liveness=$_.projection.liveness; next_action=$_.projection.nextAction
            resource_state=$_.resource.ownershipState; release_state=$_.resource.releaseState
        }
    })
}
$taskSnapshotPath = Join-Path $taskRoot 'experiments/orca-harness-20261008/runtime-checkpoint.json'
$taskTemporaryPath = $taskSnapshotPath + '.tmp'
[IO.File]::WriteAllText($taskTemporaryPath, ($taskSnapshot | ConvertTo-Json -Depth 12) + "`n", $taskEncoding)
if (Test-Path -LiteralPath $taskSnapshotPath) {
    [IO.File]::Replace($taskTemporaryPath, $taskSnapshotPath, $taskSnapshotPath + '.previous', $true)
} else { [IO.File]::Move($taskTemporaryPath, $taskSnapshotPath) }
Write-Output "Snapshot saved; $($taskSnapshot.tasks.Count) Tasks, $($taskSnapshot.workers.Count) attempts."
