#!/usr/bin/env python
"""
DeviceRouter_addDevicesFromCSV.py

Bulk-add devices from a CSV file.

Expected CSV format (with header row):
    name,displayName,collectorId,groupId,description
    192.168.1.100,web-server-01,1,2,Web tier
    192.168.1.101,web-server-02,1,2,Web tier
    192.168.1.200,db-server-01,1,5,Database tier

Usage:
    python DeviceRouter_addDevicesFromCSV.py devices.csv
"""

import sys
import csv
import lmApiLib

if len(sys.argv) < 2:
    print('Usage: %s <csv_file>' % sys.argv[0])
    sys.exit(1)

csv_file = sys.argv[1]
lm = lmApiLib.lmConnector()

added = 0
failed = 0

with open(csv_file, newline='') as f:
    reader = csv.DictReader(f)
    for row in reader:
        payload = {
            'name': row['name'],
            'displayName': row['displayName'],
            'preferredCollectorId': int(row['collectorId']),
            'hostGroupIds': row['groupId'],
            'description': row.get('description', '')
        }
        try:
            result = lm.post('/device/devices', body=payload)
            print('Added: %s (ID: %d)' % (result['displayName'], result['id']))
            added += 1
        except Exception as e:
            print('FAILED: %s — %s' % (row['displayName'], str(e)))
            failed += 1

print('\nDone. Added: %d  Failed: %d' % (added, failed))
