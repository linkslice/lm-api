<#
.SYNOPSIS
    Devices_addDevicesFromCSV.ps1
    Bulk-add devices from a CSV file.

.DESCRIPTION
    Expected CSV format (with header row):
        name,displayName,collectorId,groupId,description
        192.168.1.100,web-server-01,1,2,Web tier
        192.168.1.101,web-server-02,1,2,Web tier

.PARAMETER CsvFile
    Path to the CSV file. Defaults to 'devices.csv' in the current directory.

.EXAMPLE
    .\Devices_addDevicesFromCSV.ps1 -CsvFile .\devices.csv
#>

param(
    [string]$CsvFile = 'devices.csv'
)

Import-Module "$PSScriptRoot\..\lmApiLib.psm1" -Force

if (-not (Test-Path $CsvFile)) {
    Write-Error "CSV file not found: $CsvFile"
    exit 1
}

Connect-LMAccount

$rows = Import-Csv $CsvFile
Write-Host "Found $($rows.Count) device(s) to add.`n"

$added  = 0
$failed = 0

foreach ($row in $rows) {
    $payload = @{
        name                  = $row.name
        displayName           = $row.displayName
        preferredCollectorId  = [int]$row.collectorId
        hostGroupIds          = $row.groupId
        description           = if ($row.PSObject.Properties['description']) { $row.description } else { '' }
    }

    try {
        $result = New-LMResource '/device/devices' $payload
        Write-Host "Added: $($result.displayName) (ID: $($result.id))"
        $added++
    }
    catch {
        Write-Warning "FAILED: $($row.displayName) — $_"
        $failed++
    }
}

Write-Host "`nDone. Added: $added  Failed: $failed"
