#!/usr/bin/env python
"""
lmApiLib.py - LogicMonitor REST API v3 Client Library
Compatible with Python 3.6+

Supports LMv1 token authentication (recommended) and Bearer token authentication.
LMv1 is the default and recommended method per LogicMonitor documentation.

Usage:
    import lmApiLib
    lm = lmApiLib.lmConnector()
    result = lm.get('/device/devices', params={'size': 10})

    # With a specific creds section
    lm = lmApiLib.lmConnector(section='production')

    # Paging through large result sets
    for page in lm.pagingGet('/device/devices'):
        for device in page.get('items', []):
            print(device['displayName'])
"""

import os
import json
import time
import hmac
import hashlib
import base64
import logging
import requests

from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from urllib3.exceptions import InsecureRequestWarning
from configparser import ConfigParser


if 'logging' not in dir():
    import logging
    logging.basicConfig(
        format='%(asctime)s %(levelname)s %(name)s: %(message)s'
    )
    logging.getLogger().setLevel(logging.ERROR)


class lmConnector(object):
    """
    LogicMonitor REST API v3 connector.

    Handles LMv1 HMAC signing, Bearer token auth, pagination,
    error checking, and multi-instance credential support.

    Args:
        section (str): Section name in creds.cfg. Defaults to 'default'.
        cfgFilePath (str): Path to creds.cfg. Defaults to same directory as lmApiLib.py.
        loglevel (int): Python logging level. Defaults to ERROR (40).
    """

    def __init__(self, section='default', cfgFilePath='', loglevel=40):
        self.log = logging.getLogger('lmApiLib.lmConnector')
        self.log.setLevel(loglevel)
        self._tid = 0
        self.config = self._getConfigDetails(section, cfgFilePath)
        self.session = self._getRequestSession()

    # -------------------------------------------------------------------------
    # Configuration
    # -------------------------------------------------------------------------

    def _getConfigDetails(self, section, cfgFilePath):
        """Read creds.cfg and return the specified section as a dict."""
        if isinstance(cfgFilePath, dict):
            return self._sanitizeConfig(cfgFilePath)

        self.log.info('_getConfigDetails; section:%s, cfgFilePath:%s' % (section, cfgFilePath))

        if not cfgFilePath:
            cfgFilePath = os.path.realpath(
                os.path.join(os.getcwd(), os.path.dirname(__file__), 'creds.cfg')
            )

        cfg = ConfigParser()
        cfg.read(cfgFilePath)

        if section not in cfg.sections():
            raise Exception(
                'Configuration section "%s" not found in "%s".' % (section, cfgFilePath)
            )

        return self._sanitizeConfig(dict(cfg.items(section)))

    def _sanitizeConfig(self, config):
        """Validate and normalize config dict."""
        self.log.info('_sanitizeConfig; config:%s' % config)

        if 'account' not in config:
            raise Exception('Configuration missing required "account" key.')

        auth_method = config.get('auth_method', 'lmv1').lower()
        config['auth_method'] = auth_method

        if auth_method == 'lmv1':
            if 'access_id' not in config:
                raise Exception('LMv1 auth requires "access_id" in configuration.')
            if 'access_key' not in config:
                raise Exception('LMv1 auth requires "access_key" in configuration.')
        elif auth_method == 'bearer':
            if 'bearer_token' not in config:
                raise Exception('Bearer auth requires "bearer_token" in configuration.')
        else:
            raise Exception('Unknown auth_method "%s". Use "lmv1" or "bearer".' % auth_method)

        # Build base URL
        config['base_url'] = 'https://%s.logicmonitor.com/santaba/rest' % config['account']

        # Defaults
        config.setdefault('timeout', '10')
        config['timeout'] = float(config['timeout'])

        config.setdefault('retries', '3')
        config['retries'] = int(config['retries'])

        ssl_verify = config.get('ssl_verify', 'true').lower()
        config['ssl_verify'] = ssl_verify != 'false'
        if not config['ssl_verify']:
            requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

        return config

    def _getRequestSession(self):
        """Build a requests Session with retry logic."""
        session = requests.Session()
        retry = Retry(
            total=self.config['retries'],
            backoff_factor=0.5,
            status_forcelist=[429, 500, 502, 503, 504]
        )
        adapter = HTTPAdapter(max_retries=retry)
        session.mount('https://', adapter)
        session.verify = self.config['ssl_verify']
        return session

    # -------------------------------------------------------------------------
    # Authentication
    # -------------------------------------------------------------------------

    def _buildAuthHeader(self, method, resource_path, body=''):
        """
        Build the Authorization header for a request.

        For LMv1: computes HMAC-SHA256 signature per LM spec.
        For Bearer: returns a static header.

        Args:
            method (str): HTTP method (GET, POST, PATCH, PUT, DELETE).
            resource_path (str): API path e.g. '/device/devices'.
            body (str): Request body as string (for POST/PUT/PATCH).

        Returns:
            dict: Headers dict with Authorization and X-Version.
        """
        headers = {
            'Content-Type': 'application/json',
            'X-Version': '3'
        }

        auth_method = self.config['auth_method']

        if auth_method == 'bearer':
            headers['Authorization'] = 'Bearer %s' % self.config['bearer_token']

        elif auth_method == 'lmv1':
            epoch = str(int(time.time() * 1000))
            access_id = self.config['access_id']
            access_key = self.config['access_key']

            # LMv1 signature: HMAC-SHA256(access_key, METHOD + epoch + body + path)
            request_vars = method.upper() + epoch + body + resource_path
            signature = base64.b64encode(
                hmac.new(
                    access_key.encode('utf-8'),
                    msg=request_vars.encode('utf-8'),
                    digestmod=hashlib.sha256
                ).hexdigest().encode('utf-8')
            ).decode('utf-8')

            headers['Authorization'] = 'LMv1 %s:%s:%s' % (access_id, signature, epoch)

        return headers

    # -------------------------------------------------------------------------
    # Core HTTP methods
    # -------------------------------------------------------------------------

    def _request(self, method, resource_path, params=None, body=None):
        """
        Make an authenticated API request.

        Args:
            method (str): HTTP method.
            resource_path (str): API path e.g. '/device/devices'.
            params (dict): Query string parameters.
            body (dict): Request body (will be JSON-encoded).

        Returns:
            dict: Parsed JSON response.

        Raises:
            Exception: On non-2xx responses or JSON parse errors.
        """
        url = self.config['base_url'] + resource_path
        body_str = json.dumps(body) if body else ''

        headers = self._buildAuthHeader(method, resource_path, body_str)

        self.log.debug('_request; method:%s url:%s params:%s' % (method, url, params))

        try:
            response = self.session.request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                data=body_str if body_str else None,
                timeout=self.config['timeout']
            )
        except requests.exceptions.RequestException as e:
            raise Exception('Request failed: %s' % str(e))

        # Handle rate limiting
        if response.status_code == 429:
            retry_after = int(response.headers.get('X-Rate-Limit-Window', 60))
            self.log.warning('Rate limited. Waiting %s seconds.' % retry_after)
            time.sleep(retry_after)
            return self._request(method, resource_path, params=params, body=body)

        # Check content type
        content_type = response.headers.get('Content-Type', '')

        if 'application/json' in content_type:
            try:
                result = response.json()
            except ValueError as e:
                raise Exception('Failed to decode JSON response: %s' % str(e))

            if not response.ok:
                error_msg = result.get('errorMessage', response.text)
                error_code = result.get('errorCode', response.status_code)
                raise Exception('API error %s: %s' % (error_code, error_msg))

            return result

        elif 'text/html' in content_type:
            raise Exception(
                'Received HTML response (HTTP %s). Check your account URL and credentials.'
                % response.status_code
            )
        else:
            if not response.ok:
                raise Exception('HTTP %s: %s' % (response.status_code, response.text))
            return {'status': response.status_code, 'body': response.text}

    def get(self, resource_path, params=None):
        """
        HTTP GET request.

        Args:
            resource_path (str): API path e.g. '/device/devices'.
            params (dict): Query parameters (size, offset, filter, fields, etc.).

        Returns:
            dict: Parsed JSON response.

        Example:
            lm.get('/device/devices', params={'size': 50, 'filter': 'displayName~apache'})
        """
        return self._request('GET', resource_path, params=params)

    def post(self, resource_path, body=None, params=None):
        """
        HTTP POST request.

        Args:
            resource_path (str): API path.
            body (dict): Request body.
            params (dict): Query parameters.

        Returns:
            dict: Parsed JSON response.
        """
        return self._request('POST', resource_path, params=params, body=body)

    def patch(self, resource_path, body=None, params=None):
        """
        HTTP PATCH request. Updates only the specified fields.

        Args:
            resource_path (str): API path including resource ID.
            body (dict): Fields to update.
            params (dict): Query parameters.

        Returns:
            dict: Parsed JSON response.
        """
        return self._request('PATCH', resource_path, params=params, body=body)

    def put(self, resource_path, body=None, params=None):
        """
        HTTP PUT request. Replaces the entire resource.

        Args:
            resource_path (str): API path including resource ID.
            body (dict): Complete resource body.
            params (dict): Query parameters.

        Returns:
            dict: Parsed JSON response.
        """
        return self._request('PUT', resource_path, params=params, body=body)

    def delete(self, resource_path, params=None):
        """
        HTTP DELETE request.

        Args:
            resource_path (str): API path including resource ID.
            params (dict): Query parameters.

        Returns:
            dict: Parsed JSON response.
        """
        return self._request('DELETE', resource_path, params=params)

    # -------------------------------------------------------------------------
    # Pagination
    # -------------------------------------------------------------------------

    def pagingGet(self, resource_path, page_size=1000, params=None):
        """
        Generator that pages through all results for a GET endpoint.

        Automatically handles offset increments until all records are fetched.
        Max page size per LM API is 1000.

        Args:
            resource_path (str): API path.
            page_size (int): Records per page. Max 1000.
            params (dict): Additional query parameters (filter, fields, sort, etc.).

        Yields:
            dict: Each page response (contains 'items' and 'total' keys).

        Example:
            for page in lm.pagingGet('/device/devices', params={'filter': 'displayName~web'}):
                for device in page.get('items', []):
                    print(device['displayName'])
        """
        params = params.copy() if params else {}
        params['size'] = min(page_size, 1000)
        offset = 0
        total = None

        while True:
            params['offset'] = offset
            response = self.get(resource_path, params=params)

            if total is None:
                total = response.get('total', 0)
                self.log.info('pagingGet; total records: %d' % total)

            yield response

            items = response.get('items', [])
            offset += len(items)

            if not items or offset >= total:
                break

    def getAllResults(self, resource_path, page_size=1000, params=None):
        """
        Convenience method that pages through all results and returns a flat list.

        For large datasets, prefer pagingGet() to avoid loading everything into memory.

        Args:
            resource_path (str): API path.
            page_size (int): Records per page.
            params (dict): Additional query parameters.

        Returns:
            list: All items across all pages.

        Example:
            all_devices = lm.getAllResults('/device/devices')
        """
        results = []
        for page in self.pagingGet(resource_path, page_size=page_size, params=params):
            results.extend(page.get('items', []))
        return results
