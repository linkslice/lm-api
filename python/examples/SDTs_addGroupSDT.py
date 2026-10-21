#!/usr/bin/env python
"""
SDTs_addGroupSDT.py

Put an entire device group into Scheduled Downtime (SDT).

Useful for maintenance windows affecting a whole tier or site.
Optionally supports recurring weekly SDTs.

Usage:
    Set GROUP_ID, DURATION_MINUTES, and RECURRING below.
"""

import time
import lmApiLib

GROUP_ID = 2
DURATION_MINUTES = 120
COMMENT = 'Weekly maintenance window'
RECURRING = False          # Set True for weekly recurring SDT
RECUR_DAY = 'Sunday'      # Used only if RECURRING = True
RECUR_HOUR = 2            # Hour (24h) to start recurring SDT
RECUR_END_HOUR = 4        # Hour (24h) to end recurring SDT

lm = lmApiLib.lmConnector()

# Verify group exists
group = lm.get('/device/groups/%d' % GROUP_ID, params={'fields': 'id,name,fullPath'})
print('Targeting group: %s (ID: %d)' % (group.get('fullPath', group.get('name')), GROUP_ID))

if RECURRING:
    payload = {
        'sdtType': 2,               # Weekly recurring
        'type': 'DeviceGroupSDT',
        'deviceGroupId': GROUP_ID,
        'weekDay': RECUR_DAY,
        'hour': RECUR_HOUR,
        'minute': 0,
        'endHour': RECUR_END_HOUR,
        'endMinute': 0,
        'comment': COMMENT
    }
    print('Creating recurring weekly SDT: %s %02d:00 - %02d:00' % (RECUR_DAY, RECUR_HOUR, RECUR_END_HOUR))
else:
    now_ms = int(time.time() * 1000)
    end_ms = now_ms + (DURATION_MINUTES * 60 * 1000)
    payload = {
        'sdtType': 1,               # One-time
        'type': 'DeviceGroupSDT',
        'deviceGroupId': GROUP_ID,
        'startDateTime': now_ms,
        'endDateTime': end_ms,
        'comment': COMMENT
    }
    print('Creating one-time SDT for %d minutes' % DURATION_MINUTES)

sdt = lm.post('/sdt/sdts', body=payload)
print('SDT created: %s' % sdt.get('id'))
print('Comment: %s' % COMMENT)
