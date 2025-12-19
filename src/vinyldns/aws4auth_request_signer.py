# Copyright 2018 Comcast Cable Communications Management, LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""AWS4Auth-based request signer for VinylDNS API authentication."""

import logging
from datetime import datetime
from hashlib import sha256
import hmac

import requests.compat as urlparse

logger = logging.getLogger(__name__)

__all__ = [u'Aws4AuthRequestSigner']


class Aws4AuthRequestSigner(object):
    """Request signer using AWS Signature Version 4."""

    def __init__(self, index_url, access_key, secret_access_key):
        """Initialize the signer with credentials."""
        url = urlparse.urlparse(index_url)
        self.host = url.hostname
        self.port = url.port
        self.access_key = access_key
        self.secret_access_key = secret_access_key
        self.region = u'us-east-1'
        self.service = u'VinylDNS'

    @staticmethod
    def __canonical_date(headers):
        """
        Derive canonical date (ISO 8601 string).

        Either from headers (if possible) or synthesize it if no usable header exists.
        """
        iso_format = u'%Y%m%dT%H%M%SZ'
        http_format = u'%a, %d %b %Y %H:%M:%S GMT'

        def try_parse(date_string, format):
            if date_string is None:
                return None
            try:
                return datetime.strptime(date_string, format)
            except ValueError:
                return None

        amz_date = try_parse(headers.get(u'X-Amz-Date'), iso_format)
        http_date = try_parse(headers.get(u'Date'), http_format)
        fallback_date = datetime.utcnow()

        date = next(d for d in [amz_date, http_date, fallback_date] if d is not None)
        return date.strftime(iso_format)

    def _sign(self, key, msg):
        """Create HMAC-SHA256 signature."""
        return hmac.new(key, msg.encode('utf-8'), sha256).digest()

    def _get_signature_key(self, date_stamp):
        """Derive the signing key."""
        k_date = self._sign(('AWS4' + self.secret_access_key).encode('utf-8'), date_stamp)
        k_region = self._sign(k_date, self.region)
        k_service = self._sign(k_region, self.service)
        k_signing = self._sign(k_service, 'aws4_request')
        return k_signing

    def _get_canonical_uri(self, path):
        """Get the canonical URI (URL-encoded path)."""
        return path if path else '/'

    def _get_canonical_querystring(self, params):
        """Generate canonical query string from parameters."""
        if not params:
            return ''
        import urllib.parse
        sorted_params = sorted(params.items())
        canonical_querystring = '&'.join(
            '{}={}'.format(
                urllib.parse.quote(str(k), safe='-_.~'),
                urllib.parse.quote(str(v), safe='-_.~')
            )
            for k, v in sorted_params
        )
        return canonical_querystring

    def _get_canonical_headers(self, headers, host_header):
        """Generate canonical headers string."""
        canonical_headers = {}
        for key, value in headers.items():
            canonical_headers[key.lower()] = value.strip()

        if 'host' not in canonical_headers:
            canonical_headers['host'] = host_header

        sorted_headers = sorted(canonical_headers.items())
        return '\n'.join('{}:{}'.format(k, v) for k, v in sorted_headers) + '\n'

    def _get_signed_headers(self, headers, include_host=True):
        """Get the list of signed header names."""
        header_names = [k.lower() for k in headers.keys()]
        if include_host and 'host' not in header_names:
            header_names.append('host')
        return ';'.join(sorted(header_names))

    def build_auth_header(self, method, path, headers, body, params=None):
        """Construct an Authorization header using AWS Signature Version 4."""
        timestamp = Aws4AuthRequestSigner.__canonical_date(headers)
        date_stamp = timestamp[0:8]

        # Build host header
        if self.port and self.port not in (80, 443):
            host_header = '{}:{}'.format(self.host, self.port)
        else:
            host_header = self.host

        # Canonical URI
        canonical_uri = self._get_canonical_uri(path)

        # Canonical query string
        canonical_querystring = self._get_canonical_querystring(params)

        # Canonical headers
        canonical_headers = self._get_canonical_headers(headers, host_header)

        # Signed headers
        signed_headers = self._get_signed_headers(headers)

        # Payload hash
        payload = body if body else ''
        if isinstance(payload, str):
            payload = payload.encode('utf-8')
        payload_hash = sha256(payload).hexdigest()

        # Canonical request
        canonical_request = '\n'.join([
            method,
            canonical_uri,
            canonical_querystring,
            canonical_headers,
            signed_headers,
            payload_hash
        ])

        # String to sign
        credential_scope = '/'.join([date_stamp, self.region, self.service, 'aws4_request'])
        string_to_sign = '\n'.join([
            'AWS4-HMAC-SHA256',
            timestamp,
            credential_scope,
            sha256(canonical_request.encode('utf-8')).hexdigest()
        ])

        # Signature
        signing_key = self._get_signature_key(date_stamp)
        signature = hmac.new(signing_key, string_to_sign.encode('utf-8'), sha256).hexdigest()

        # Authorization header
        auth_header = 'AWS4-HMAC-SHA256 Credential={}/{}, SignedHeaders={}, Signature={}'.format(
            self.access_key,
            credential_scope,
            signed_headers,
            signature
        )

        return auth_header
