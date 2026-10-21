<#
.SYNOPSIS
    Collectors_getCollectors.ps1
    List all collectors with status, build version, and device count.
    Highlights any collectors that are offline or have no devices assigned.
#>

Import-Module "$PSScriptRoot\..\lmApiLib.psm1" -Force

Connect-LMAccount

Write-Host "`nFetching collectors...`n"

$collectors = Get-LMResults '/setting/collector/collectors' -Params @{
    fields = 'id,description,hostname,status,upTime,build,platform,numberOfHosts,collectorGroupId'
}

if ($collectors.Count -eq 0) {
    Write-Host 'No collectors found.'
    exit 0
}

$collectors | Sort-Object id | ForEach-Object {
    $statusColor = if ($_.status -eq 'normal') { 'Green' } else { 'Red' }
    $warnEmpty   = $_.numberOfHosts -eq 0

    Write-Host ('[{0}] {1}' -f $_.id, ($_.description ?? $_.hostname)) -NoNewline
    Write-Host (' [{0}]' -f $_.status) -ForegroundColor $statusColor -NoNewline
    Write-Host (' build:{0} devices:{1}' -f $_.build, $_.numberOfHosts) -NoNewline
    if ($warnEmpty) { Write-Host ' *** NO DEVICES ***' -ForegroundColor Yellow } else { Write-Host }
}

$offline = $collectors | Where-Object { $_.status -ne 'normal' }
Write-Host ("`nTotal: {0} collectors ({1} offline)" -f $collectors.Count, $offline.Count)
