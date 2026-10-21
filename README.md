# lm-api

Client libraries and examples for the [LogicMonitor REST API v3](https://www.logicmonitor.com/support/rest-api-developers-guide/overview/using-logicmonitors-rest-api).

Available in Python and PowerShell with identical functionality, credential file format, and example naming conventions. Pick whichever fits your environment and workflow.

> **Note:** LogicMonitor sunset REST API v1 and v2 in October 2024. All code in this repo targets v3 only.

---

## Repository Structure

```
lm-api/
├── python/
│   ├── lmApiLib.py          # Python client library
│   ├── lmApiCli.py          # Command-line interface
│   ├── creds.cfg.sample     # Credential file template
│   └── examples/            # Example scripts
└── powershell/
    ├── lmApiLib.psm1         # PowerShell module
    ├── lmApiLib.psd1         # Module manifest
    ├── creds.cfg.sample      # Credential file template (same format)
    └── examples/             # Example scripts
```

---

## Quick Start

### 1. Clone the repo

```bash
git clone https://github.com/linkslice/lm-api.git
cd lm-api
```

### 2. Set up credentials

Both the Python and PowerShell libraries read from the same INI-style `creds.cfg` format. Copy the sample from whichever directory you're using:

```bash
# Python
cp python/creds.cfg.sample python/creds.cfg

# PowerShell
cp powershell/creds.cfg.sample powershell/creds.cfg
```

Edit `creds.cfg` and fill in your account name and API token. See [Authentication](#authentication) below.

### 3. Run an example

```bash
# Python
cd python
python examples/DeviceRouter_getDevices.py

# PowerShell
cd powershell
.\examples\DeviceRouter_getDevices.ps1
```

---

## Authentication

LogicMonitor REST API v3 supports two token-based auth methods. Basic authentication is not supported in v2+.

### LMv1 (Recommended)

LMv1 is LogicMonitor's recommended authentication method for API scripting. It uses an Access ID and Access Key pair with a per-request HMAC-SHA256 signature. Both libraries compute and inject the signature automatically — you just set the credentials in `creds.cfg` and make calls.

Generate tokens at: **Settings → User Access → API Tokens → LMv1 tab**

```ini
[default]
account=mycompany
auth_method=lmv1
access_id=REPLACE_WITH_ACCESS_ID
access_key=REPLACE_WITH_ACCESS_KEY
```

### Bearer Token

Bearer token auth is simpler (no per-request signing) but requires an LM APM license (Traces feature). If you have it, set `auth_method=bearer` in your config.

Generate tokens at: **Settings → User Access → API Tokens → Bearer tab**

```ini
[default]
account=mycompany
auth_method=bearer
bearer_token=REPLACE_WITH_BEARER_TOKEN
```

### Multiple Instances

Both libraries support multiple named sections in `creds.cfg`, useful for managing dev/staging/prod environments:

```ini
[default]
account=mycompany-dev
auth_method=lmv1
access_id=...
access_key=...

[production]
account=mycompany
auth_method=lmv1
access_id=...
access_key=...
```

```python
# Python
lm = lmApiLib.lmConnector(section='production')
```

```powershell
# PowerShell
Connect-LMAccount -Section 'production'
```

---

## Language Choice

| | Python | PowerShell |
|---|---|---|
| **Minimum version** | Python 3.6+ | PowerShell 5.1 / PS 7+ |
| **Dependencies** | `requests` (pip) | None (built-in) |
| **Best for** | Automation, data processing, cross-platform | Windows environments, AD/SCCM integration, existing PS infrastructure |
| **CLI tool** | `lmApiCli.py` | — |

---

## Example Naming Convention

Examples follow the `RouterName_methodDescription` naming pattern, mirroring the [zenoss-RM-api](https://github.com/zenoss/zenoss-RM-api) library conventions:

```
DeviceRouter_getDevices.py
DeviceRouter_addDevicesFromCSV.py
AlertRouter_queryAlerts.py
SDTRouter_addDeviceSDT.py
CollectorRouter_getCollectors.py
```

The `RouterName` prefix is conceptual (LM uses REST paths, not routers) — it groups examples by the resource area they operate on.

---

## Related Resources

- [LM REST API v3 Swagger Docs](https://www.logicmonitor.com/swagger-ui-master/api-v3/lm-sdkv3-swagger.html)
- [LM REST API Overview](https://www.logicmonitor.com/support/rest-api-developers-guide/overview/using-logicmonitors-rest-api)
- [LM REST API Authentication](https://www.logicmonitor.com/support/rest-api-authentication)
- [LM REST API v3 Filters](https://www.logicmonitor.com/support/rest-api-developers-guide/v3/rest-api-v3-basic-filters)
- [LM REST API Rate Limits](https://www.logicmonitor.com/support/rest-api-developers-guide/overview/rest-api-rate-limit)

---

## Contributing

PRs welcome. Follow the existing naming convention for examples, include a docstring or `.SYNOPSIS` block, and test against a real LM instance before submitting.

Keep `creds.cfg` out of commits — it's in `.gitignore`.
