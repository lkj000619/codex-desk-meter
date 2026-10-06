param([Parameter(Mandatory=$true)][string]$InputJson,[Parameter(Mandatory=$true)][string]$OutputJson)
$ErrorActionPreference = 'Stop'
$lunaCommands = ConvertFrom-Json -InputObject ([IO.File]::ReadAllText($InputJson,[Text.Encoding]::UTF8))
$lunaFindings = @()
foreach ($lunaCommand in $lunaCommands) {
    $lunaTokens = $null
    $lunaErrors = $null
    $lunaAst = [Management.Automation.Language.Parser]::ParseInput($lunaCommand.body,[ref]$lunaTokens,[ref]$lunaErrors)
    $lunaPipelines = @($lunaAst.FindAll({param($n) $n -is [Management.Automation.Language.PipelineAst] -and $n.PipelineElements.Count -gt 1},$true))
    $lunaSeparators = @($lunaTokens | Where-Object { $_.Kind.ToString() -in @('Semi','AndAnd','OrOr') })
    if ($lunaPipelines.Count -gt 0 -or $lunaSeparators.Count -gt 0 -or $lunaErrors.Count -gt 0) {
        $lunaFindings += @{run_id=$lunaCommand.run_id;raw_line=$lunaCommand.raw_line;body=$lunaCommand.body;parse_errors=@($lunaErrors | ForEach-Object { $_.Message });pipeline_extents=@($lunaPipelines | ForEach-Object { $_.Extent.Text });separator_extents=@($lunaSeparators | ForEach-Object { $_.Extent.Text })}
    }
}
[IO.File]::WriteAllText($OutputJson,(ConvertTo-Json -InputObject @($lunaFindings) -Depth 20),[Text.UTF8Encoding]::new($false))
# Inert parsing only; captured commands are never executed.
