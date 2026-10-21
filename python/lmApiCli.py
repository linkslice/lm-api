#!/usr/bin/env python
"""
lmApiCli.py - Command Line Interface for the LogicMonitor REST API v3

Wraps lmApiLib.py for quick ad-hoc API calls from the shell.
Useful for one-liners, shell scripts, and piping output to jq.

Examples:
    # List devices
    ./lmApiCli.py --resource /device/devices --method GET

    # Filter and limit fields
    ./lmApiCli.py --resource /device/devices --method GET \\
        --params "filter=displayName~apache&fields=id,displayName,name"

    # Get a specific device by ID
    ./lmApiCli.py --resource /device/devices/123 --method GET

    # Add a device
    ./lmApiCli.py --resource /device/devices --method POST \\
        --body '{"name":"192.168.1.100","displayName":"my-server","preferredCollectorId":1,"hostGroupIds":"2"}'

    # Patch (partial update)
    ./lmApiCli.py --resource /device/devices/123 --method PATCH \\
        --body '{"description":"Updated via CLI"}'

    # Delete
    ./lmApiCli.py --resource /device/devices/123 --method DELETE

    # Extract a specific field from the response (dot notation)
    ./lmApiCli.py --resource /device/devices --method GET --extract total
    ./lmApiCli.py --resource /device/devices --method GET --extract items.0.displayName
    ./lmApiCli.py --resource /device/devices --method GET --extract items.*.displayName

    # Use a non-default credentials section
    ./lmApiCli.py --resource /device/devices --method GET --section production

    # Increase verbosity for debugging
    ./lmApiCli.py --resource /device/devices --method GET -v 10
"""

from __future__ import print_function

import sys
import json
import argparse
import logging

import lmApiLib


def extractField(data, path):
    """
    Extract a value from a nested dict/list using dot notation.

    Supports wildcard '*' to iterate over list items.

    Args:
        data: dict or list to extract from.
        path (str): Dot-separated field path e.g. 'items.0.displayName'
                    or 'items.*.displayName'

    Returns:
        Extracted value(s), or None if path not found.
    """
    if not path or path == 'all':
        return data

    parts = path.split('.')
    current = data

    for part in parts:
        if current is None:
            return None
        if part == '*':
            if isinstance(current, list):
                # Collect remaining path for each item
                remaining = '.'.join(parts[parts.index(part) + 1:])
                if remaining:
                    return [extractField(item, remaining) for item in current]
                else:
                    return current
            else:
                return None
        elif isinstance(current, list):
            try:
                current = current[int(part)]
            except (ValueError, IndexError):
                return None
        elif isinstance(current, dict):
            current = current.get(part)
        else:
            return None

    return current


def parseParams(param_string):
    """
    Parse a query parameter string into a dict.

    Supports 'key=value&key2=value2' format.

    Args:
        param_string (str): URL-style query string.

    Returns:
        dict: Parsed parameters.
    """
    if not param_string:
        return {}
    params = {}
    for pair in param_string.split('&'):
        if '=' in pair:
            k, v = pair.split('=', 1)
            params[k.strip()] = v.strip()
    return params


def main():
    parser = argparse.ArgumentParser(
        description='Command Line Interface to LogicMonitor REST API v3.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    parser.add_argument(
        '--resource', '-r',
        required=True,
        help='API resource path e.g. /device/devices or /device/devices/123'
    )
    parser.add_argument(
        '--method', '-m',
        required=True,
        choices=['GET', 'POST', 'PATCH', 'PUT', 'DELETE'],
        help='HTTP method'
    )
    parser.add_argument(
        '--params', '-p',
        default='',
        help='Query parameters as URL-encoded string e.g. "filter=displayName~apache&size=50"'
    )
    parser.add_argument(
        '--body', '-b',
        default=None,
        help='Request body as JSON string (for POST, PUT, PATCH)'
    )
    parser.add_argument(
        '--extract', '-x',
        default='all',
        help='Dot-notation field path to extract from response. '
             'Use "*" as wildcard for lists. Default: "all" (full response). '
             'Examples: total, items.0.displayName, items.*.displayName'
    )
    parser.add_argument(
        '--section', '-s',
        default='default',
        help='Credentials section in creds.cfg (default: "default")'
    )
    parser.add_argument(
        '--creds', '-c',
        default='',
        help='Path to creds.cfg file (default: same directory as lmApiCli.py)'
    )
    parser.add_argument(
        '-v', '--loglevel',
        type=int,
        default=40,
        help='Logging level: DEBUG=10, INFO=20, WARN=30, ERROR=40 (default)'
    )

    args = parser.parse_args()

    logging.basicConfig(
        format='%(asctime)s %(levelname)s %(name)s: %(message)s',
        level=args.loglevel
    )

    # Build connector
    try:
        lm = lmApiLib.lmConnector(
            section=args.section,
            cfgFilePath=args.creds,
            loglevel=args.loglevel
        )
    except Exception as e:
        print('ERROR: Failed to initialize connector: %s' % str(e), file=sys.stderr)
        sys.exit(1)

    # Parse inputs
    params = parseParams(args.params)
    body = None
    if args.body:
        try:
            body = json.loads(args.body)
        except json.JSONDecodeError as e:
            print('ERROR: Invalid JSON body: %s' % str(e), file=sys.stderr)
            sys.exit(1)

    # Make the request
    try:
        method = args.method.upper()
        if method == 'GET':
            result = lm.get(args.resource, params=params)
        elif method == 'POST':
            result = lm.post(args.resource, body=body, params=params)
        elif method == 'PATCH':
            result = lm.patch(args.resource, body=body, params=params)
        elif method == 'PUT':
            result = lm.put(args.resource, body=body, params=params)
        elif method == 'DELETE':
            result = lm.delete(args.resource, params=params)
    except Exception as e:
        print('ERROR: %s' % str(e), file=sys.stderr)
        sys.exit(1)

    # Extract and print
    output = extractField(result, args.extract)

    if output is None:
        print('WARNING: Field path "%s" not found in response.' % args.extract, file=sys.stderr)
        sys.exit(1)

    if isinstance(output, (dict, list)):
        print(json.dumps(output, indent=2))
    else:
        print(output)


if __name__ == '__main__':
    main()
