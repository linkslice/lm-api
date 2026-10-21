# lm-api / powershell

PowerShell client module for the LogicMonitor REST API v3.
Compatible with Windows PowerShell 5.1 and PowerShell 7+.

---

## Files

| File | Description |
|---|---|
| `lmApiLib.psm1` | PowerShell module |
| `lmApiLib.psd1` | Module manifest |
| `creds.cfg.sample` | Credential file template |
| `examples/` | Example scripts |

---

## Setup

### Credentials

```powershell
Copy-Item creds.cfg.sample creds.cfg
```

Edit `creds.cfg` with your account details. See the [root README](../README.md#authentication) for auth options.

### Execution Policy

If you haven't already, allow local scripts to run:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

---

## lmApiLib.psm1

### Importing the Module

```powershell
Import-Module .\lmApiLib.psm1

# Force reload during development
Import-Module .\lmApiLib.psm1 -Force
```

Examples in the `examples/` directory import the module relative to their own path — you can run them directly without a separate import step.

### Connecting

```powershell
# Default section of creds.cfg
Connect-LMAccount

# Specific section
Connect-LMAccount -Section 'production'

# Explicit creds file path
Connect-LMAccount -CfgFilePath 'C:\Scripts\lm-creds.cfg'

# Check current connection
Get-LMConnectionInfo

# Disconnect
Disconnect-LMAccount
```

### Making Requests

```powershell
# GET
$result = Get-LMResource '/device/devices' -Params @{size=50; filter='displayName~apache'}

# POST
$result = New-LMResource '/device/devices' @{
    name                 = '192.168.1.100'
    displayName          = 'my-server-01'
    preferredCollectorId = 1
    hostGroupIds         = '2'
}

# PATCH (partial update)
$result = Update-LMResource '/device/devices/123' @{description='Updated'}

# PUT (full replacement)
$result = Set-LMResource '/device/devices/123' @{...}

# DELETE
Remove-LMResource '/device/devices/123'

# Raw access to all methods (GET, POST, PATCH, PUT, DELETE)
$result = Invoke-LMAPI -Method GET -ResourcePath '/device/devices' -Params @{size=10}
```

### Pagination

```powershell
# Get-LMResults pages automatically and returns a flat array
$devices = Get-LMResults '/device/devices'

# With filtering and field selection
$alerts = Get-LMResults '/alert/alerts' -Params @{
    filter = 'cleared:false'
    fields = 'id,severity,monitorObjectName,instanceName'
    sort   = '-severity'
}

# Custom page size (max 1000)
$devices = Get-LMResults '/device/devices' -PageSize 500
```

### Filtering

```powershell
# Contains
Get-LMResource '/device/devices' -Params @{filter='displayName~apache'}

# Exact match
Get-LMResource '/device/devices' -Params @{filter='displayName:my-server-01'}

# Multiple conditions (AND)
Get-LMResource '/alert/alerts' -Params @{filter='cleared:false,severity>:2'}
```

### Field Selection

```powershell
Get-LMResource '/device/devices' -Params @{
    fields = 'id,displayName,name,hostGroupIds,currentCollectorId'
}
```

### Verbose Output

```powershell
# See request URLs and pagination progress
Get-LMResults '/device/devices' -Verbose
Connect-LMAccount -Verbose
```

### Error Handling

```powershell
try {
    $result = Get-LMResource '/device/devices/99999'
}
catch {
    Write-Warning "API error: $_"
}
```

---

## Available Functions

| Function | Description |
|---|---|
| `Connect-LMAccount` | Load credentials and initialize connection |
| `Disconnect-LMAccount` | Clear connection state |
| `Get-LMConnectionInfo` | Display current connection details |
| `Invoke-LMAPI` | Core HTTP method dispatcher |
| `Get-LMResource` | HTTP GET |
| `New-LMResource` | HTTP POST |
| `Update-LMResource` | HTTP PATCH (partial update) |
| `Set-LMResource` | HTTP PUT (full replacement) |
| `Remove-LMResource` | HTTP DELETE |
| `Get-LMResults` | Paginated GET — returns flat array of all items |

---

## Examples

| Script | Description |
|---|---|
| `Devices_getDevices.ps1` | List all devices with pagination |
| `Devices_addDevicesFromCSV.ps1` | Bulk-add devices from a CSV file |
| `Devices_propertyReport.ps1` | Export devices and custom properties to CSV |
| `Alerts_queryAlerts.ps1` | Query and display active alerts as a table |
| `SDTs_addDeviceSDT.ps1` | Put a device into SDT by display name |
| `Collectors_getCollectors.ps1` | List collectors with status and device count |

---

## Notes on PowerShell 5.1 vs 7+

The module targets PS 5.1 for maximum compatibility. A few notes if you're on PS 7+:

- `??` (null coalescing) is used in some examples — PS 5.1 compatible alternatives are included where needed
- SSL verification bypass uses `SkipCertificateCheck` on PS 7+ and a `ServicePointManager` callback on PS 5.1 (handled automatically)
- `[DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds()` requires .NET 4.6+, which ships with PS 5.1 on Windows 10/Server 2016+
