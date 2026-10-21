#!/usr/bin/env python
"""
DatasourceRouter_instanceReport.py

For a given datasource name, list all devices it's applied to
and the instances discovered on each device.

Useful for verifying datasource coverage and instance discovery health.

Usage:
    Set DATASOURCE_NAME below and run.
"""

import lmApiLib

DATASOURCE_NAME = 'Ping'

lm = lmApiLib.lmConnector()

# Find the datasource
print('Looking up datasource: %s' % DATASOURCE_NAME)
ds_result = lm.get('/setting/datasources', params={
    'filter': 'name:%s' % DATASOURCE_NAME,
    'fields': 'id,name,displayName'
})

items = ds_result.get('items', [])
if not items:
    print('Datasource not found: %s' % DATASOURCE_NAME)
    exit(1)

ds = items[0]
ds_id = ds['id']
print('Found datasource ID %d: %s\n' % (ds_id, ds.get('displayName', ds['name'])))

# Get all devices that have this datasource applied
print('Fetching device datasource assignments...')
device_ds_list = lm.getAllResults('/device/devices', params={
    'fields': 'id,displayName'
})

total_instances = 0
for device in device_ds_list:
    dev_id = device['id']

    # Check if this datasource is applied to the device
    applied = lm.get('/device/devices/%d/devicedatasources' % dev_id, params={
        'filter': 'dataSourceId:%d' % ds_id,
        'fields': 'id,dataSourceName,instanceNumber'
    })

    applied_items = applied.get('items', [])
    if not applied_items:
        continue

    dds_id = applied_items[0]['id']
    instance_count = applied_items[0].get('instanceNumber', 0)

    print('[%d] %s — %d instance(s)' % (dev_id, device['displayName'], instance_count))

    if instance_count > 0:
        instances = lm.get(
            '/device/devices/%d/devicedatasources/%d/instances' % (dev_id, dds_id),
            params={'fields': 'id,displayName,wildValue,stopMonitoring'}
        )
        for inst in instances.get('items', []):
            status = 'DISABLED' if inst.get('stopMonitoring') else 'active'
            print('    - %s (wildValue: %s) [%s]' % (
                inst.get('displayName', inst.get('wildValue', '')),
                inst.get('wildValue', ''),
                status
            ))
            total_instances += 1

print('\nTotal instances across all devices: %d' % total_instances)
