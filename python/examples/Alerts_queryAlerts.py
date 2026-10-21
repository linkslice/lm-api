#!/usr/bin/env python
"""
Alerts_queryAlerts.py

Query active (uncleared) alerts, optionally filtered by severity.
Prints a summary table sorted by severity descending.

Severity levels:
    4 = Critical
    3 = Error
    2 = Warning
    1 = Info
"""

import lmApiLib

# Set minimum severity to include (4=Critical, 3=Error, 2=Warning, 1=Info)
MIN_SEVERITY = 3

lm = lmApiLib.lmConnector()

SEVERITY_LABELS = {4: 'CRITICAL', 3: 'ERROR', 2: 'WARNING', 1: 'INFO'}

print('Fetching active alerts (severity >= %s)...\n' % SEVERITY_LABELS.get(MIN_SEVERITY, MIN_SEVERITY))

alerts = lm.getAllResults('/alert/alerts', params={
    'filter': 'cleared:false,severity>:%d' % (MIN_SEVERITY - 1),
    'fields': 'id,severity,monitorObjectName,resourceTemplateName,instanceName,alertValue,startEpoch',
    'sort': '-severity'
})

if not alerts:
    print('No active alerts found.')
else:
    print('%-10s %-10s %-30s %-25s %-20s %s' % (
        'ID', 'SEVERITY', 'DEVICE', 'DATASOURCE', 'INSTANCE', 'VALUE'
    ))
    print('-' * 105)
    for alert in alerts:
        print('%-10s %-10s %-30s %-25s %-20s %s' % (
            alert.get('id', ''),
            SEVERITY_LABELS.get(alert.get('severity'), alert.get('severity')),
            (alert.get('monitorObjectName') or '')[:29],
            (alert.get('resourceTemplateName') or '')[:24],
            (alert.get('instanceName') or '')[:19],
            alert.get('alertValue', '')
        ))
    print('\nTotal: %d alerts' % len(alerts))
