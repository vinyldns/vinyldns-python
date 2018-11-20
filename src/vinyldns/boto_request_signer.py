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
"""TODO: Add module docstring."""

import logging
from datetime import datetime
from hashlib import sha256

import requests.compat as urlparse
from boto.dynamodb2.layer1 import DynamoDBConnection

logger = logging.getLogger(__name__)

__all__ = [u'BotoRequestSigner']


class BotoRequestSigner(object):
    """TODO: Add class docstring."""

    def __init__(self, index_url, access_key, secret_access_key):
        """TODO: Add method docstring."""
        url = urlparse.urlparse(index_url)
        self.boto_connection = DynamoDBConnection(
            host=url.hostname,
            port=url.port,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_access_key,
            is_secure=False)

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

    def build_auth_header(self, method, path, headers, body, params=None):
        """Construct an Authorization header, using boto."""
        request = self.boto_connection.build_base_http_request(
            method=method,
            path=path,
            auth_path=path,
            headers=headers,
            data=body,
            params=params or {})

        auth_handler = self.boto_connection._auth_handler

        timestamp = BotoRequestSigner.__canonical_date(headers)
        request.timestamp = timestamp[0:8]

        request.region_name = u'us-east-1'
        request.service_name = u'VinylDNS'

        credential_scope = u'/'.join([request.timestamp, request.region_name, request.service_name, u'aws4_request'])

        canonical_request = auth_handler.canonical_request(request)
        hashed_request = sha256(canonical_request.encode(u'utf-8')).hexdigest()

        string_to_sign = u'\n'.join([u'AWS4-HMAC-SHA256', timestamp, credential_scope, hashed_request])
        signature = auth_handler.signature(request, string_to_sign)
        headers_to_sign = auth_handler.headers_to_sign(request)

        auth_header = u','.join([
            u'AWS4-HMAC-SHA256 Credential=%s' % auth_handler.scope(request),
            u'SignedHeaders=%s' % auth_handler.signed_headers(headers_to_sign),
            u'Signature=%s' % signature])

        return auth_header
