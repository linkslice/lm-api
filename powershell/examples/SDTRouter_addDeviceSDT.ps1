<#
.SYNOPSIS
    SDTRouter_addDeviceSDT.ps1
    Put a device into Scheduled Downtime (SDT) by display name.

.PARAMETER DeviceDisplayName
    Display name of the device to SDT.

.PARAMETER DurationMinutes
    Length of the SDT window in minutes. Default: 60.

.PARAMETER Comment
    Comment to attach to the SDT. Default: 'Maintenance window'.

.EXAMPLE
    .\SDTRouter_addDeviceSDT.ps1 -DeviceDisplayName 'my-server-01' -DurationMinutes 120 -Comment 'Patching'
#>

param(
    [Parameter(Mandatory)]
    [string]$DeviceDisplayName,

    [int]$DurationMinutes = 60,

    [string]$Comment = 'Maintenance window'
)

Import-Module "$PSScriptRoot\..\lmApiLib.psm1" -Force

Connect-LMAccount

# Look up device by display name
Write-Host "Looking up device: $DeviceDisplayName"

$result = Get-LMResource '/device/devices' -Params @{
    filter = "displayName:$DeviceDisplayName"
    fields = 'id,displayName'
}

if ($result.items.Count -eq 0) {
    Write-Error "Device not found: $DeviceDisplayName"
    exit 1
}

$device   = $result.items[0]
$deviceId = $device.id
Write-Host "Found device ID: $deviceId"

# Calculate epoch ms start/end
$nowMs = [DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds()
$endMs = $nowMs + ($DurationMinutes * 60 * 1000)

$payload = @{
    sdtType       = 1                # 1=One-Time
    type          = 'DeviceSDT'
    deviceId      = $deviceId
    startDateTime = $nowMs
    endDateTime   = $endMs
    comment       = $Comment
}

$sdt = New-LMResource '/sdt/sdts' $payload

Write-Host "SDT created: $($sdt.id)"
Write-Host "Device: $($device.displayName)"
Write-Host "Duration: $DurationMinutes minutes"
Write-Host "Comment: $Comment"
