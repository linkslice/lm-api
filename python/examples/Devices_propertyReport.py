#!/usr/bin/env python
"""
Devices_propertyReport.py

Generate a CSV report of all devices with their custom properties.
Useful for auditing, CMDB sync, or inventory exports.

Output: device_property_report.csv
"""

import csv
import lmApiLib

OUTPUT_FILE = 'device_property_report.csv'

# Custom properties to include in the report (leave empty for all)
INCLUDE_PROPERTIES = ['snmp.community', 'location', 'environment']

lm = lmApiLib.lmConnector()

print('Fetching all devices...')
devices = lm.getAllResults('/device/devices', params={
    'fields': 'id,displayName,name,hostGroupIds,currentCollectorId',
    'sort': 'displayName'
})

print('Fetched %d devices. Building property report...' % len(devices))

rows = []
all_prop_names = set(INCLUDE_PROPERTIES)

for device in devices:
    try:
        props_result = lm.get('/device/devices/%d/properties' % device['id'], params={
            'fields': 'name,value,type'
        })
        props = {p['name']: p['value'] for p in props_result.get('items', [])}

        if not INCLUDE_PROPERTIES:
            all_prop_names.update(props.keys())

        row = {
            'id': device['id'],
            'displayName': device['displayName'],
            'name': device['name'],
            'hostGroupIds': device.get('hostGroupIds', ''),
            'collectorId': device.get('currentCollectorId', '')
        }
        row.update(props)
        rows.append(row)
    except Exception as e:
        print('WARNING: Could not fetch properties for device %d: %s' % (device['id'], str(e)))

# Build fieldnames
base_fields = ['id', 'displayName', 'name', 'hostGroupIds', 'collectorId']
prop_fields = sorted(all_prop_names) if INCLUDE_PROPERTIES else sorted(all_prop_names - set(base_fields))
fieldnames = base_fields + prop_fields

with open(OUTPUT_FILE, 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
    writer.writeheader()
    writer.writerows(rows)

print('Report written to: %s (%d devices)' % (OUTPUT_FILE, len(rows)))
