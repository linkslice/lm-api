<#
.SYNOPSIS
    AlertRouter_queryAlerts.ps1
    Query active (uncleared) alerts and display a summary table.

.PARAMETER MinSeverity
    Minimum severity to include. 4=Critical, 3=Error, 2=Warning, 1=Info. Default: 3
#>

param(
    [ValidateRange(1,4)]
    [int]$MinSeverity = 3
)

Import-Module "$PSScriptRoot\..\lmApiLib.psm1" -Force

$severityLabels = @{4='CRITICAL'; 3='ERROR'; 2='WARNING'; 1='INFO'}

Connect-LMAccount

Write-Host "`nFetching active alerts (severity >= $($severityLabels[$MinSeverity]))...`n"

$alerts = Get-LMResults '/alert/alerts' -Params @{
    filter = "cleared:false,severity>:$($MinSeverity - 1)"
    fields = 'id,severity,monitorObjectName,resourceTemplateName,instanceName,alertValue,startEpoch'
    sort   = '-severity'
}

if ($alerts.Count -eq 0) {
    Write-Host 'No active alerts found.'
} else {
    $alerts | ForEach-Object {
        [PSCustomObject]@{
            ID         = $_.id
            Severity   = $severityLabels[[int]$_.severity]
            Device     = $_.monitorObjectName
            Datasource = $_.resourceTemplateName
            Instance   = $_.instanceName
            Value      = $_.alertValue
        }
    } | Format-Table -AutoSize

    Write-Host "Total: $($alerts.Count) alert(s)"
}
