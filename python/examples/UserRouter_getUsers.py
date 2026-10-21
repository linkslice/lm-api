#!/usr/bin/env python
"""
UserRouter_getUsers.py

List all users with their roles and status.
Optionally filter to show only active or suspended users.
"""

import lmApiLib

# Set to 'active', 'suspended', or None for all
FILTER_STATUS = None

lm = lmApiLib.lmConnector()

params = {
    'fields': 'id,username,email,firstName,lastName,status,roles,lastActionEpoch',
    'sort': 'username'
}

if FILTER_STATUS:
    params['filter'] = 'status:%s' % FILTER_STATUS

print('Fetching users%s...\n' % (' (status: %s)' % FILTER_STATUS if FILTER_STATUS else ''))

users = lm.getAllResults('/setting/admins', params=params)

if not users:
    print('No users found.')
    exit(0)

print('%-5s %-25s %-30s %-12s %s' % ('ID', 'USERNAME', 'EMAIL', 'STATUS', 'ROLES'))
print('-' * 100)

for user in users:
    roles = ', '.join([r.get('name', '') for r in user.get('roles', [])])
    print('%-5d %-25s %-30s %-12s %s' % (
        user.get('id', 0),
        (user.get('username') or '')[:24],
        (user.get('email') or '')[:29],
        user.get('status', ''),
        roles[:40]
    ))

print('\nTotal users: %d' % len(users))
