#!/usr/bin/env python
"""
Devices_getDevices.py

List all devices, paginating through the full result set.
Prints device ID, display name, and IP address.
"""

import lmApiLib

lm = lmApiLib.lmConnector()

print('Fetching all devices...\n')

total_fetched = 0
for page in lm.pagingGet('/device/devices', params={
    'fields': 'id,displayName,name,currentCollectorId,hostGroupIds',
    'sort': 'displayName'
}):
    for device in page.get('items', []):
        print('[%d] %s (%s)' % (
            device.get('id'),
            device.get('displayName'),
            device.get('name')
        ))
        total_fetched += 1

print('\nTotal devices: %d' % total_fetched)
