<#
.SYNOPSIS
    Devices_getDevices.ps1
    List all devices, paginating through the full result set.
#>

Import-Module "$PSScriptRoot\..\lmApiLib.psm1" -Force

Connect-LMAccount

Write-Host "`nFetching all devices...`n"

$devices = Get-LMResults '/device/devices' -Params @{
    fields = 'id,displayName,name,currentCollectorId,hostGroupIds'
    sort   = 'displayName'
}

foreach ($device in $devices) {
    Write-Host ('[{0}] {1} ({2})' -f $device.id, $device.displayName, $device.name)
}

Write-Host ("`nTotal devices: {0}" -f $devices.Count)
