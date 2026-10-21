#Requires -Version 5.1
<#
.SYNOPSIS
    lmApiLib.psm1 - LogicMonitor REST API v3 PowerShell Module

.DESCRIPTION
    PowerShell client for the LogicMonitor REST API v3.
    Supports LMv1 HMAC signing (recommended) and Bearer token authentication.
    Handles pagination, rate limiting, error checking, and multi-instance
    credential support via a shared creds.cfg file format.

.NOTES
    Compatible with Windows PowerShell 5.1 and PowerShell 7+.
    Import-Module .\lmApiLib.psm1

.EXAMPLE
    Import-Module .\lmApiLib.psm1
    Connect-LMAccount
    $devices = Get-LMResults '/device/devices'
    $devices | ForEach-Object { Write-Host $_.displayName }

.EXAMPLE
    # Use a non-default credentials section
    Connect-LMAccount -Section 'production'
    $alerts = Invoke-LMAPI -Method GET -ResourcePath '/alert/alerts' -Params @{filter='cleared:false'}
#>

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# Module-level state
$script:LMConfig = $null


# =============================================================================
# Configuration & Connection
# =============================================================================

function Connect-LMAccount {
    <#
    .SYNOPSIS
        Load credentials from creds.cfg and initialize the LM connection.

    .DESCRIPTION
        Reads the specified section from creds.cfg and stores connection
        details in module state. Must be called before any API requests.

    .PARAMETER Section
        Section name in creds.cfg. Defaults to 'default'.

    .PARAMETER CfgFilePath
        Path to creds.cfg. Defaults to the same directory as lmApiLib.psm1.

    .EXAMPLE
        Connect-LMAccount
        Connect-LMAccount -Section 'production'
        Connect-LMAccount -CfgFilePath 'C:\Scripts\lm-creds.cfg'
    #>
    [CmdletBinding()]
    param(
        [string]$Section = 'default',
        [string]$CfgFilePath = ''
    )

    if (-not $CfgFilePath) {
        $CfgFilePath = Join-Path $PSScriptRoot 'creds.cfg'
    }

    if (-not (Test-Path $CfgFilePath)) {
        throw "Credentials file not found: $CfgFilePath`nCopy creds.cfg.sample to creds.cfg and fill in your values."
    }

    $config = Read-IniFile -Path $CfgFilePath -Section $Section

    # Validate required fields
    if (-not $config.ContainsKey('account')) {
        throw "Configuration section [$Section] missing required 'account' key."
    }

    $authMethod = if ($config.ContainsKey('auth_method')) { $config['auth_method'].ToLower() } else { 'lmv1' }
    $config['auth_method'] = $authMethod

    switch ($authMethod) {
        'lmv1' {
            if (-not $config.ContainsKey('access_id'))  { throw "LMv1 auth requires 'access_id' in [$Section]." }
            if (-not $config.ContainsKey('access_key')) { throw "LMv1 auth requires 'access_key' in [$Section]." }
        }
        'bearer' {
            if (-not $config.ContainsKey('bearer_token')) { throw "Bearer auth requires 'bearer_token' in [$Section]." }
        }
        default {
            throw "Unknown auth_method '$authMethod'. Use 'lmv1' or 'bearer'."
        }
    }

    $config['base_url'] = "https://$($config['account']).logicmonitor.com/santaba/rest"
    $config['timeout']  = if ($config.ContainsKey('timeout'))  { [int]$config['timeout'] }  else { 10 }
    $config['retries']  = if ($config.ContainsKey('retries'))  { [int]$config['retries'] }  else { 3 }
    $config['ssl_verify'] = -not ($config.ContainsKey('ssl_verify') -and $config['ssl_verify'] -eq 'false')

    $script:LMConfig = $config

    Write-Verbose "Connected to LogicMonitor account: $($config['account']) (auth: $authMethod)"
    Write-Host "Connected to: $($config['account']).logicmonitor.com [$authMethod]"
}


function Disconnect-LMAccount {
    <#
    .SYNOPSIS
        Clear the current LM connection state.
    #>
    $script:LMConfig = $null
    Write-Host 'Disconnected from LogicMonitor.'
}


function Get-LMConnectionInfo {
    <#
    .SYNOPSIS
        Display current connection details (no secrets).
    #>
    if (-not $script:LMConfig) {
        Write-Host 'Not connected. Run Connect-LMAccount first.'
        return
    }
    [PSCustomObject]@{
        Account    = $script:LMConfig['account']
        AuthMethod = $script:LMConfig['auth_method']
        BaseURL    = $script:LMConfig['base_url']
        Timeout    = $script:LMConfig['timeout']
        Retries    = $script:LMConfig['retries']
    }
}


# =============================================================================
# Internal Helpers
# =============================================================================

function Read-IniFile {
    <#
    .SYNOPSIS
        Parse a simple INI file and return a hashtable for the specified section.
    #>
    param(
        [string]$Path,
        [string]$Section
    )

    $result = @{}
    $inSection = $false

    foreach ($line in Get-Content $Path) {
        $line = $line.Trim()

        # Skip blank lines and comments
        if ([string]::IsNullOrWhiteSpace($line) -or $line.StartsWith('#') -or $line.StartsWith(';')) {
            continue
        }

        # Section header
        if ($line -match '^\[(.+)\]$') {
            $inSection = ($Matches[1].Trim() -eq $Section)
            continue
        }

        # Key=value pair
        if ($inSection -and $line -match '^([^=]+)=(.*)$') {
            $key   = $Matches[1].Trim()
            $value = $Matches[2].Trim()
            $result[$key] = $value
        }
    }

    if ($result.Count -eq 0) {
        throw "Configuration section [$Section] not found in $Path"
    }

    return $result
}


function Get-LMAuthHeader {
    <#
    .SYNOPSIS
        Build the Authorization header for a request.

    .DESCRIPTION
        For LMv1: computes HMAC-SHA256 signature per LM spec.
        For Bearer: returns a static Authorization header.
    #>
    param(
        [string]$Method,
        [string]$ResourcePath,
        [string]$Body = ''
    )

    Assert-LMConnected

    $headers = @{
        'Content-Type' = 'application/json'
        'X-Version'    = '3'
    }

    switch ($script:LMConfig['auth_method']) {
        'bearer' {
            $headers['Authorization'] = "Bearer $($script:LMConfig['bearer_token'])"
        }
        'lmv1' {
            $epoch     = [DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds().ToString()
            $accessId  = $script:LMConfig['access_id']
            $accessKey = $script:LMConfig['access_key']

            # LMv1: HMAC-SHA256(access_key, METHOD + epoch + body + path)
            $requestVars = $Method.ToUpper() + $epoch + $Body + $ResourcePath
            $hmacKey     = [System.Text.Encoding]::UTF8.GetBytes($accessKey)
            $hmacMsg     = [System.Text.Encoding]::UTF8.GetBytes($requestVars)
            $hmac        = New-Object System.Security.Cryptography.HMACSHA256
            $hmac.Key    = $hmacKey
            $hashBytes   = $hmac.ComputeHash($hmacMsg)
            $hexStr      = -join ($hashBytes | ForEach-Object { $_.ToString('x2') })
            $signature   = [Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes($hexStr))

            $headers['Authorization'] = "LMv1 ${accessId}:${signature}:${epoch}"
        }
    }

    return $headers
}


function Assert-LMConnected {
    if (-not $script:LMConfig) {
        throw 'Not connected. Run Connect-LMAccount first.'
    }
}


# =============================================================================
# Core HTTP Methods
# =============================================================================

function Invoke-LMAPI {
    <#
    .SYNOPSIS
        Make an authenticated request to the LogicMonitor REST API v3.

    .PARAMETER Method
        HTTP method: GET, POST, PATCH, PUT, DELETE.

    .PARAMETER ResourcePath
        API resource path e.g. '/device/devices' or '/device/devices/123'.

    .PARAMETER Params
        Hashtable of query parameters.

    .PARAMETER Body
        Hashtable or PSObject to send as JSON body (POST, PUT, PATCH).

    .EXAMPLE
        Invoke-LMAPI -Method GET -ResourcePath '/device/devices' -Params @{size=50}
        Invoke-LMAPI -Method POST -ResourcePath '/device/devices' -Body @{name='192.168.1.1'; displayName='server01'; preferredCollectorId=1; hostGroupIds='2'}
        Invoke-LMAPI -Method PATCH -ResourcePath '/device/devices/123' -Body @{description='Updated'}
        Invoke-LMAPI -Method DELETE -ResourcePath '/device/devices/123'
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [ValidateSet('GET','POST','PATCH','PUT','DELETE')]
        [string]$Method,

        [Parameter(Mandatory)]
        [string]$ResourcePath,

        [hashtable]$Params = @{},
        [object]$Body = $null
    )

    Assert-LMConnected

    $bodyStr = ''
    if ($null -ne $Body) {
        $bodyStr = $Body | ConvertTo-Json -Depth 10 -Compress
    }

    $headers = Get-LMAuthHeader -Method $Method -ResourcePath $ResourcePath -Body $bodyStr

    # Build URL with query params
    $url = $script:LMConfig['base_url'] + $ResourcePath
    if ($Params.Count -gt 0) {
        $queryString = ($Params.GetEnumerator() | ForEach-Object {
            "$([Uri]::EscapeDataString($_.Key))=$([Uri]::EscapeDataString($_.Value.ToString()))"
        }) -join '&'
        $url = "${url}?${queryString}"
    }

    Write-Verbose "$Method $url"

    $invokeParams = @{
        Method  = $Method
        Uri     = $url
        Headers = $headers
        TimeoutSec = $script:LMConfig['timeout']
    }

    if ($bodyStr) {
        $invokeParams['Body'] = $bodyStr
    }

    # Skip SSL verification if configured
    if (-not $script:LMConfig['ssl_verify']) {
        if ($PSVersionTable.PSVersion.Major -ge 6) {
            $invokeParams['SkipCertificateCheck'] = $true
        } else {
            # PS 5.1 workaround
            [System.Net.ServicePointManager]::ServerCertificateValidationCallback = { $true }
        }
    }

    $attempt = 0
    $maxRetries = $script:LMConfig['retries']

    while ($attempt -le $maxRetries) {
        try {
            $response = Invoke-RestMethod @invokeParams
            return $response
        }
        catch [System.Net.WebException] {
            $statusCode = [int]$_.Exception.Response.StatusCode

            # Rate limited
            if ($statusCode -eq 429) {
                $retryAfter = 60
                try {
                    $retryHeader = $_.Exception.Response.Headers['X-Rate-Limit-Window']
                    if ($retryHeader) { $retryAfter = [int]$retryHeader }
                } catch {}
                Write-Warning "Rate limited. Waiting ${retryAfter}s before retry..."
                Start-Sleep -Seconds $retryAfter
                $attempt++
                continue
            }

            # Retriable server errors
            if ($statusCode -in @(500, 502, 503, 504) -and $attempt -lt $maxRetries) {
                $wait = [math]::Pow(2, $attempt)
                Write-Warning "HTTP $statusCode. Retrying in ${wait}s (attempt $($attempt+1)/$maxRetries)..."
                Start-Sleep -Seconds $wait
                $attempt++
                continue
            }

            # Read error response body
            $stream = $_.Exception.Response.GetResponseStream()
            $reader = New-Object System.IO.StreamReader($stream)
            $errorBody = $reader.ReadToEnd()

            try {
                $errorObj = $errorBody | ConvertFrom-Json
                throw "API error $($errorObj.errorCode): $($errorObj.errorMessage)"
            } catch {
                throw "HTTP ${statusCode}: $errorBody"
            }
        }
        catch {
            throw
        }
    }
}


# =============================================================================
# Convenience Wrappers
# =============================================================================

function Get-LMResource {
    <#
    .SYNOPSIS
        HTTP GET wrapper for the LM API.

    .EXAMPLE
        Get-LMResource '/device/devices' @{size=50; filter='displayName~apache'}
        Get-LMResource '/device/devices/123'
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [string]$ResourcePath,

        [hashtable]$Params = @{}
    )

    Invoke-LMAPI -Method GET -ResourcePath $ResourcePath -Params $Params
}


function New-LMResource {
    <#
    .SYNOPSIS
        HTTP POST wrapper for the LM API.

    .EXAMPLE
        New-LMResource '/device/devices' @{name='192.168.1.1'; displayName='server01'; preferredCollectorId=1; hostGroupIds='2'}
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [string]$ResourcePath,

        [Parameter(Mandatory)]
        [object]$Body,

        [hashtable]$Params = @{}
    )

    Invoke-LMAPI -Method POST -ResourcePath $ResourcePath -Body $Body -Params $Params
}


function Update-LMResource {
    <#
    .SYNOPSIS
        HTTP PATCH wrapper. Updates only the specified fields.

    .EXAMPLE
        Update-LMResource '/device/devices/123' @{description='Updated via API'}
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [string]$ResourcePath,

        [Parameter(Mandatory)]
        [object]$Body,

        [hashtable]$Params = @{}
    )

    Invoke-LMAPI -Method PATCH -ResourcePath $ResourcePath -Body $Body -Params $Params
}


function Set-LMResource {
    <#
    .SYNOPSIS
        HTTP PUT wrapper. Replaces the entire resource.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [string]$ResourcePath,

        [Parameter(Mandatory)]
        [object]$Body,

        [hashtable]$Params = @{}
    )

    Invoke-LMAPI -Method PUT -ResourcePath $ResourcePath -Body $Body -Params $Params
}


function Remove-LMResource {
    <#
    .SYNOPSIS
        HTTP DELETE wrapper.

    .EXAMPLE
        Remove-LMResource '/device/devices/123'
        Remove-LMResource '/sdt/sdts/SDT_1'
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [string]$ResourcePath,

        [hashtable]$Params = @{}
    )

    Invoke-LMAPI -Method DELETE -ResourcePath $ResourcePath -Params $Params
}


# =============================================================================
# Pagination
# =============================================================================

function Get-LMResults {
    <#
    .SYNOPSIS
        Page through all results for a GET endpoint and return a flat array.

    .DESCRIPTION
        Automatically handles offset/size pagination until all records are fetched.
        Max page size per LM API is 1000.

    .PARAMETER ResourcePath
        API resource path.

    .PARAMETER PageSize
        Records per page. Maximum 1000.

    .PARAMETER Params
        Additional query parameters (filter, fields, sort, etc.).

    .EXAMPLE
        $devices = Get-LMResults '/device/devices'
        $alerts  = Get-LMResults '/alert/alerts' -Params @{filter='cleared:false'}
        $devices = Get-LMResults '/device/devices' -Params @{filter='displayName~web'; fields='id,displayName,name'}
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [string]$ResourcePath,

        [int]$PageSize = 1000,

        [hashtable]$Params = @{}
    )

    $pageParams = @{} + $Params
    $pageParams['size']   = [math]::Min($PageSize, 1000)
    $pageParams['offset'] = 0

    $allItems = [System.Collections.Generic.List[object]]::new()
    $total    = $null

    do {
        $response = Get-LMResource -ResourcePath $ResourcePath -Params $pageParams

        if ($null -eq $total) {
            $total = $response.total
            Write-Verbose "Get-LMResults: total records = $total"
        }

        $items = $response.items
        if (-not $items) { break }

        foreach ($item in $items) {
            $allItems.Add($item)
        }

        $pageParams['offset'] += $items.Count
        Write-Verbose "Get-LMResults: fetched $($allItems.Count) / $total"

    } while ($allItems.Count -lt $total -and $items.Count -gt 0)

    return $allItems.ToArray()
}


# =============================================================================
# Exports
# =============================================================================

Export-ModuleMember -Function @(
    'Connect-LMAccount'
    'Disconnect-LMAccount'
    'Get-LMConnectionInfo'
    'Invoke-LMAPI'
    'Get-LMResource'
    'New-LMResource'
    'Update-LMResource'
    'Set-LMResource'
    'Remove-LMResource'
    'Get-LMResults'
)
