#!/usr/bin/env python
"""
DeviceRouter_moveDevice.py

Move a device to a different device group by display name.

Usage:
    python DeviceRouter_moveDevice.py
    (edit DEVICE_DISPLAY_NAME and TARGET_GROUP_ID below)
"""

import lmApiLib

DEVICE_DISPLAY_NAME = 'my-server-01'
TARGET_GROUP_ID = 5

lm = lmApiLib.lmConnector()

# Find the device by display name
print('Searching for device: %s' % DEVICE_DISPLAY_NAME)
result = lm.get('/device/devices', params={
    'filter': 'displayName:%s' % DEVICE_DISPLAY_NAME,
    'fields': 'id,displayName,hostGroupIds'
})

items = result.get('items', [])
if not items:
    print('Device not found: %s' % DEVICE_DISPLAY_NAME)
    exit(1)

device = items[0]
print('Found device ID %d, current groups: %s' % (device['id'], device['hostGroupIds']))

# PATCH the device to update its group membership
updated = lm.patch('/device/devices/%d' % device['id'], body={
    'hostGroupIds': str(TARGET_GROUP_ID)
})

print('Moved to group %d. New hostGroupIds: %s' % (TARGET_GROUP_ID, updated['hostGroupIds']))
