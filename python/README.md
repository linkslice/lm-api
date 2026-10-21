# lm-api / python

Python 3.6+ client library for the LogicMonitor REST API v3.

---

## Files

| File | Description |
|---|---|
| `lmApiLib.py` | Main client library |
| `lmApiCli.py` | Command-line interface for ad-hoc API calls |
| `creds.cfg.sample` | Credential file template |
| `examples/` | Example scripts |

---

## Setup

### Prerequisites

```bash
pip install requests
```

### Credentials

```bash
cp creds.cfg.sample creds.cfg
```

Edit `creds.cfg` with your account details. See the [root README](../README.md#authentication) for auth options.

### Environment

If running examples from outside the `python/` directory, add it to your `PYTHONPATH`:

```bash
export PYTHONPATH=/path/to/lm-api/python:$PYTHONPATH
```

---

## lmApiLib.py

### Basic Usage

```python
import lmApiLib

# Connect using the 'default' section of creds.cfg
lm = lmApiLib.lmConnector()

# Use a different creds section
lm = lmApiLib.lmConnector(section='production')

# Specify a creds file path explicitly
lm = lmApiLib.lmConnector(cfgFilePath='/etc/lm/creds.cfg')

# Enable debug logging
lm = lmApiLib.lmConnector(loglevel=10)
```

### HTTP Methods

```python
# GET
result = lm.get('/device/devices', params={'size': 50, 'filter': 'displayName~apache'})

# POST
result = lm.post('/device/devices', body={
    'name': '192.168.1.100',
    'displayName': 'my-server-01',
    'preferredCollectorId': 1,
    'hostGroupIds': '2'
})

# PATCH (partial update — only specified fields are changed)
result = lm.patch('/device/devices/123', body={'description': 'Updated'})

# PUT (full replacement)
result = lm.put('/device/devices/123', body={...})

# DELETE
result = lm.delete('/device/devices/123')
```

### Pagination

The LM API returns paged results with a max of 1000 records per request. Use `pagingGet()` for a generator that handles offsets automatically:

```python
# Generator — yields one page dict at a time (memory efficient for large sets)
for page in lm.pagingGet('/device/devices', params={'filter': 'displayName~web'}):
    for device in page.get('items', []):
        print(device['displayName'])

# Convenience method — returns all items as a flat list
all_devices = lm.getAllResults('/device/devices')
```

### Filtering

LM v3 supports basic and advanced filter syntax via the `filter` query parameter:

```python
# Contains
lm.get('/device/devices', params={'filter': 'displayName~apache'})

# Exact match
lm.get('/device/devices', params={'filter': 'displayName:my-server-01'})

# Multiple conditions (AND)
lm.get('/alert/alerts', params={'filter': 'cleared:false,severity>:2'})
```

### Field Selection

Use `fields` to limit response payload:

```python
lm.get('/device/devices', params={'fields': 'id,displayName,name,hostGroupIds'})
```

### Error Handling

```python
try:
    result = lm.get('/device/devices/99999')
except Exception as e:
    print('API error: %s' % str(e))
```

---

## lmApiCli.py

Command-line wrapper for quick ad-hoc queries without writing a script.

### Usage

```
./lmApiCli.py --resource PATH --method METHOD [options]
```

### Options

| Flag | Description |
|---|---|
| `--resource`, `-r` | API resource path e.g. `/device/devices` |
| `--method`, `-m` | HTTP method: GET, POST, PATCH, PUT, DELETE |
| `--params`, `-p` | Query params as URL-encoded string: `"filter=displayName~apache&size=50"` |
| `--body`, `-b` | Request body as JSON string (POST, PUT, PATCH) |
| `--extract`, `-x` | Dot-notation field to extract. Use `*` wildcard. Default: `all` |
| `--section`, `-s` | Credentials section in creds.cfg (default: `default`) |
| `--creds`, `-c` | Path to creds.cfg |
| `-v` | Log level: 10=DEBUG, 20=INFO, 30=WARN, 40=ERROR (default) |

### Examples

```bash
# List all devices
./lmApiCli.py -r /device/devices -m GET

# Filter and extract just display names
./lmApiCli.py -r /device/devices -m GET \
    --params "filter=displayName~apache&fields=id,displayName" \
    --extract items.*.displayName

# Get total alert count
./lmApiCli.py -r /alert/alerts -m GET \
    --params "filter=cleared:false" \
    --extract total

# Get a specific device
./lmApiCli.py -r /device/devices/123 -m GET

# Add a device
./lmApiCli.py -r /device/devices -m POST \
    --body '{"name":"192.168.1.100","displayName":"server01","preferredCollectorId":1,"hostGroupIds":"2"}'

# Partial update
./lmApiCli.py -r /device/devices/123 -m PATCH \
    --body '{"description":"Updated via CLI"}'

# Delete
./lmApiCli.py -r /device/devices/123 -m DELETE

# Use production credentials section
./lmApiCli.py -r /device/devices -m GET --section production

# Pipe to jq for further processing
./lmApiCli.py -r /device/devices -m GET | jq '.items[] | {id, displayName}'
```

---

## Examples

| Script | Description |
|---|---|
| `DeviceRouter_getDevices.py` | List all devices with pagination |
| `DeviceRouter_addDevice.py` | Add a single device |
| `DeviceRouter_addDevicesFromCSV.py` | Bulk-add devices from a CSV file |
| `DeviceRouter_moveDevice.py` | Move a device to a different group by display name |
| `DeviceRouter_propertyReport.py` | Export all devices and custom properties to CSV |
| `AlertRouter_queryAlerts.py` | Query and display active alerts |
| `AlertRouter_acknowledgeAlerts.py` | Acknowledge all alerts for a device |
| `SDTRouter_addDeviceSDT.py` | Put a device into SDT by display name |
| `SDTRouter_addGroupSDT.py` | Put a device group into SDT (one-time or recurring) |
| `CollectorRouter_getCollectors.py` | List collectors with status and device count |
| `UserRouter_getUsers.py` | List users with roles and status |
| `DatasourceRouter_instanceReport.py` | List all instances for a given datasource |
