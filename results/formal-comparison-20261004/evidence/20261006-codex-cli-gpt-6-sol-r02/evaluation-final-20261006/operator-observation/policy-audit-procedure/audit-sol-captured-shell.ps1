param([Parameter(Mandatory=$true)][string]$InputJson,[Parameter(Mandatory=$true)][string]$OutputJson)
$ErrorActionPreference = 'Stop'
$solAuditCommands = ConvertFrom-Json -InputObject ([IO.File]::ReadAllText($InputJson,[Text.Encoding]::UTF8))
$solAuditFindings = @()
foreach ($solAuditCommand in $solAuditCommands) {
    $solAuditTokens = $null
    $solAuditErrors = $null
    $solAuditAst = [Management.Automation.Language.Parser]::ParseInput($solAuditCommand.body,[ref]$solAuditTokens,[ref]$solAuditErrors)
    $solAuditPipelines = @($solAuditAst.FindAll({param($solNode) $solNode -is [Management.Automation.Language.PipelineAst] -and $solNode.PipelineElements.Count -gt 1},$true))
    if ($solAuditPipelines.Count -gt 0 -or $solAuditErrors.Count -gt 0) {
        $solAuditErrorText = @()
        foreach ($solAuditError in $solAuditErrors) { $solAuditErrorText += $solAuditError.Message }
        $solAuditPipelineText = @()
        foreach ($solAuditPipeline in $solAuditPipelines) { $solAuditPipelineText += $solAuditPipeline.Extent.Text }
        $solAuditFindings += @{run_id=$solAuditCommand.run_id;raw_line=$solAuditCommand.raw_line;body=$solAuditCommand.body;command=$solAuditCommand.command;parse_errors=$solAuditErrorText;pipeline_extents=$solAuditPipelineText}
    }
}
[IO.File]::WriteAllText($OutputJson,(ConvertTo-Json -InputObject @($solAuditFindings) -Depth 20),[Text.UTF8Encoding]::new($false))
# ParseInput only: captured commands are never executed.
