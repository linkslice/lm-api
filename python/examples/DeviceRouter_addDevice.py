#!/usr/bin/env python
"""
DeviceRouter_addDevice.py

Add a new device to LogicMonitor.
Adjust the payload fields for your environment before running.
"""

import lmApiLib

lm = lmApiLib.lmConnector()

payload = {
    'name': '192.168.1.100',                # IP or hostname
    'displayName': 'my-server-01',
    'preferredCollectorId': 1,              # Collector ID — check yours with /setting/collector/collectors
    'hostGroupIds': '2',                    # Device group ID
    'description': 'Added via lmApiLib',
    'disableAlerting': False,
    'customProperties': [
        {'name': 'snmp.community', 'value': 'public'}
    ]
}

print('Adding device: %s' % payload['displayName'])

result = lm.post('/device/devices', body=payload)
print('Created device ID: %d' % result['id'])
print('Display name: %s' % result['displayName'])
