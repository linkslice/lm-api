#!/usr/bin/env python
"""
SDTs_addDeviceSDT.py

Put a device into Scheduled Downtime (SDT) by display name.

Useful for maintenance windows — suppresses alerting for the duration.

Usage:
    Edit the variables below and run.
    Duration is specified in minutes.
"""

import time
import lmApiLib

DEVICE_DISPLAY_NAME = 'my-server-01'
DURATION_MINUTES = 60
COMMENT = 'Maintenance window — patching'

lm = lmApiLib.lmConnector()

# Look up device ID
print('Looking up device: %s' % DEVICE_DISPLAY_NAME)
result = lm.get('/device/devices', params={
    'filter': 'displayName:%s' % DEVICE_DISPLAY_NAME,
    'fields': 'id,displayName'
})

items = result.get('items', [])
if not items:
    print('Device not found: %s' % DEVICE_DISPLAY_NAME)
    exit(1)

device = items[0]
device_id = device['id']
print('Found device ID: %d' % device_id)

# Calculate start/end epoch milliseconds
now_ms = int(time.time() * 1000)
end_ms = now_ms + (DURATION_MINUTES * 60 * 1000)

payload = {
    'sdtType': 1,                   # 1=One-Time, 2=Weekly, 3=Monthly, 4=Daily
    'type': 'DeviceSDT',
    'deviceId': device_id,
    'startDateTime': now_ms,
    'endDateTime': end_ms,
    'comment': COMMENT
}

sdt = lm.post('/sdt/sdts', body=payload)

print('SDT created: %s' % sdt.get('id'))
print('Device: %s' % device['displayName'])
print('Duration: %d minutes' % DURATION_MINUTES)
print('Comment: %s' % COMMENT)
