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

from __future__ import annotations

import logging
from datetime import datetime, UTC
from typing import Dict, Optional, Union
import urllib.parse as urlparse

from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest
from botocore.credentials import Credentials

logger = logging.getLogger(__name__)

__all__ = ["BotoRequestSigner"]


class BotoRequestSigner:
    """
    Signs HTTP requests using AWS Signature Version 4 for the VinylDNS service.
    """

    def __init__(
        self,
        index_url: str,
        access_key: str,
        secret_access_key: str,
    ) -> None:
        url = urlparse.urlparse(index_url)
        scheme = url.scheme or "https"
        host = url.hostname
        port = url.port

        if host is None:
            raise ValueError(f"Invalid index_url (missing host): {index_url}")

        self.netloc = f"{host}:{port}" if port else host
        self.base_url = f"{scheme}://{self.netloc}"
        self.region_name = "us-east-1"
        self.service_name = "VinylDNS"
        self.credentials = Credentials(access_key, secret_access_key)

    @staticmethod
    def __canonical_date(headers: Dict[str, str]) -> str:
        """
        Resolve an ISO8601-like date from headers, falling back to current UTC.

        Checks 'X-Amz-Date' (ISO8601 basic) and 'Date' (HTTP-date),
        and returns an ISO8601 basic formatted string.
        """
        iso_format = "%Y%m%dT%H%M%SZ"
        http_format = "%a, %d %b %Y %H:%M:%S GMT"

        def try_parse(
            date_string: Optional[str],
            fmt: str,
        ) -> Optional[datetime]:
            if date_string is None:
                return None
            try:
                return datetime.strptime(date_string, fmt)
            except ValueError:
                return None

        amz_date = try_parse(headers.get("X-Amz-Date"), iso_format)
        http_date = try_parse(headers.get("Date"), http_format)
        fallback_date = datetime.now(UTC)

        date = next(
            d for d in (amz_date, http_date, fallback_date) if d is not None
        )
        return date.strftime(iso_format)

    def build_auth_header(
        self,
        method: str,
        path: str,
        headers: Optional[Dict[str, str]],
        body: Optional[Union[str, bytes]],
        params: Optional[Dict[str, Union[str, bytes]]] = None,
    ) -> str:
        """
        Build the AWS SigV4 Authorization header for the given request parameters.
        """
        hdrs: Dict[str, str] = dict(headers or {})
        hdrs.setdefault("Host", self.netloc)
        # Remove Date header if present
        hdrs.pop("Date", None)

        # Normalize body to bytes
        if body is None:
            data = b""
        elif isinstance(body, str):
            data = body.encode("utf-8")
        else:
            data = body

        query = generate_canonical_query_string(params or {})

        if not path.startswith("/"):
            path = "/" + path

        url = f"{self.base_url}{path}"
        if query:
            url = f"{url}?{query}"

        aws_request = AWSRequest(
            method=method,
            url=url,
            data=data,
            headers=hdrs,
        )

        SigV4Auth(
            self.credentials,
            self.service_name,
            self.region_name,
        ).add_auth(aws_request)

        return aws_request.headers["Authorization"]


def generate_canonical_query_string(
    params: Dict[str, Union[str, bytes]],
) -> str:
    """
    Generate a canonical (sorted + percent-encoded) query string suitable for SigV4.
    """
    if not params:
        return ""

    def _to_str(value: Union[str, bytes]) -> str:
        if isinstance(value, bytes):
            return value.decode("utf-8")
        return str(value)

    encoded_pairs = []

    for param in sorted(params):
        value = _to_str(params[param])
        encoded_pairs.append(
            "%s=%s"
            % (
                urlparse.quote(param, safe="-_.~"),
                urlparse.quote(value, safe="-_.~"),
            )
        )

    return "&".join(encoded_pairs)
