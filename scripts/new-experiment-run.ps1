[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$Baseline,
    [Parameter(Mandatory = $true)][string]$Profile,
    [Parameter(Mandatory = $true)][string]$RunRoot,
    [Parameter(Mandatory = $true)][int]$Seed,
    [ValidateSet('pilot', 'benchmark')][string]$Phase = 'pilot',
    [string]$Port = ''
)
$ErrorActionPreference = 'Stop'
$arguments = @((Join-Path $PSScriptRoot 'benchmark.py'), 'prepare', '--baseline', $Baseline,
    '--profile', $Profile, '--root', $RunRoot, '--seed', "$Seed", '--phase', $Phase)
if ($Port) { $arguments += @('--port', $Port) }
& python @arguments
if ($LASTEXITCODE -ne 0) { throw 'Run preparation failed.' }
