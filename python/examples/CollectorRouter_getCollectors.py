#!/usr/bin/env python
"""
CollectorRouter_getCollectors.py

List all collectors with status, version, and device count.
Useful for capacity planning and identifying stale/offline collectors.
"""

import lmApiLib

lm = lmApiLib.lmConnector()

print('Fetching collectors...\n')

collectors = lm.getAllResults('/setting/collector/collectors', params={
    'fields': 'id,description,hostname,status,upTime,build,platform,numberOfHosts,collectorGroupId'
})

if not collectors:
    print('No collectors found.')
    exit(0)

print('%-5s %-30s %-20s %-10s %-8s %-6s' % (
    'ID', 'DESCRIPTION', 'HOSTNAME', 'STATUS', 'BUILD', 'DEVICES'
))
print('-' * 85)

for c in sorted(collectors, key=lambda x: x.get('id', 0)):
    print('%-5d %-30s %-20s %-10s %-8s %-6d' % (
        c.get('id', 0),
        (c.get('description') or c.get('hostname', ''))[:29],
        (c.get('hostname') or '')[:19],
        c.get('status', 'unknown'),
        str(c.get('build', ''))[:7],
        c.get('numberOfHosts', 0)
    ))

print('\nTotal collectors: %d' % len(collectors))
