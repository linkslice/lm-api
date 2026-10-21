<#
.SYNOPSIS
    Devices_propertyReport.ps1
    Export all devices with selected custom properties to CSV.

.PARAMETER OutputFile
    Path for the CSV output. Default: device_property_report.csv

.PARAMETER IncludeProperties
    Comma-separated list of property names to include.
    Leave empty to include all custom properties.

.EXAMPLE
    .\Devices_propertyReport.ps1
    .\Devices_propertyReport.ps1 -OutputFile C:\Reports\lm_devices.csv -IncludeProperties 'snmp.community,location,environment'
#>

param(
    [string]$OutputFile = 'device_property_report.csv',
    [string]$IncludeProperties = ''
)

Import-Module "$PSScriptRoot\..\lmApiLib.psm1" -Force

Connect-LMAccount

$filterProps = if ($IncludeProperties) { $IncludeProperties -split ',' | ForEach-Object { $_.Trim() } } else { @() }

Write-Host "Fetching all devices..."
$devices = Get-LMResults '/device/devices' -Params @{
    fields = 'id,displayName,name,hostGroupIds,currentCollectorId'
    sort   = 'displayName'
}
Write-Host "Fetched $($devices.Count) devices. Building report..."

$rows = [System.Collections.Generic.List[hashtable]]::new()
$allPropNames = [System.Collections.Generic.HashSet[string]]::new()

foreach ($device in $devices) {
    try {
        $propsResult = Get-LMResource "/device/devices/$($device.id)/properties" -Params @{
            fields = 'name,value,type'
        }

        $props = @{}
        foreach ($p in $propsResult.items) {
            if ($filterProps.Count -eq 0 -or $p.name -in $filterProps) {
                $props[$p.name] = $p.value
                [void]$allPropNames.Add($p.name)
            }
        }

        $row = @{
            id             = $device.id
            displayName    = $device.displayName
            name           = $device.name
            hostGroupIds   = $device.hostGroupIds
            collectorId    = $device.currentCollectorId
        }
        foreach ($k in $props.Keys) { $row[$k] = $props[$k] }
        $rows.Add($row)
    }
    catch {
        Write-Warning "Could not fetch properties for device $($device.id): $_"
    }
}

# Build ordered column list
$baseFields = @('id','displayName','name','hostGroupIds','collectorId')
$propFields = $allPropNames | Sort-Object
$allFields  = $baseFields + $propFields

# Write CSV
$rows | ForEach-Object {
    $row = $_
    $obj = [ordered]@{}
    foreach ($f in $allFields) {
        $obj[$f] = if ($row.ContainsKey($f)) { $row[$f] } else { '' }
    }
    [PSCustomObject]$obj
} | Export-Csv -Path $OutputFile -NoTypeInformation -Encoding UTF8

Write-Host "Report written to: $OutputFile ($($rows.Count) devices)"
