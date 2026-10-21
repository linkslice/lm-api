@{
    ModuleVersion     = '1.0.0'
    GUID              = 'a3f2c1d4-e5b6-7890-abcd-ef1234567890'
    Author            = 'lm-api contributors'
    Description       = 'PowerShell client for the LogicMonitor REST API v3. Supports LMv1 and Bearer token authentication, pagination, and rate limit handling.'
    PowerShellVersion = '5.1'
    RootModule        = 'lmApiLib.psm1'

    FunctionsToExport = @(
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

    PrivateData = @{
        PSData = @{
            Tags       = @('LogicMonitor', 'API', 'Monitoring', 'REST')
            ProjectUri = 'https://github.com/linkslice/lm-api'
        }
    }
}
