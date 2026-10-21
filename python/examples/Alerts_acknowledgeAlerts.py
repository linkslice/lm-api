#!/usr/bin/env python
"""
Alerts_acknowledgeAlerts.py

Acknowledge all active unacknowledged alerts for a specific device.

Usage:
    Edit DEVICE_DISPLAY_NAME and ACK_COMMENT below, then run.
"""

import lmApiLib

DEVICE_DISPLAY_NAME = 'my-server-01'
ACK_COMMENT = 'Acknowledged via API — investigating'

lm = lmApiLib.lmConnector()

print('Fetching unacknowledged alerts for: %s' % DEVICE_DISPLAY_NAME)

alerts = lm.getAllResults('/alert/alerts', params={
    'filter': 'cleared:false,acked:false,monitorObjectName:%s' % DEVICE_DISPLAY_NAME,
    'fields': 'id,severity,resourceTemplateName,instanceName'
})

if not alerts:
    print('No unacknowledged alerts found.')
    exit(0)

print('Found %d alert(s). Acknowledging...\n' % len(alerts))

acked = 0
failed = 0

for alert in alerts:
    try:
        lm.post('/alert/alerts/%s/ack' % alert['id'], body={'ackComment': ACK_COMMENT})
        print('Acked: %s (%s / %s)' % (
            alert['id'],
            alert.get('resourceTemplateName', ''),
            alert.get('instanceName', '')
        ))
        acked += 1
    except Exception as e:
        print('FAILED to ack %s: %s' % (alert['id'], str(e)))
        failed += 1

print('\nDone. Acknowledged: %d  Failed: %d' % (acked, failed))
