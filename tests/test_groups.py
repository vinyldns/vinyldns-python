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

import json

import pytest
import responses
from vinyldns.client import VinylDNSClient
from vinyldns.serdes import to_json_string, from_json_string
from vinyldns.zone import AccessLevel, ACLRule, ZoneConnection, ZoneACL, Zone


@pytest.fixture
def mocked_responses():
    with responses.RequestsMock() as rsps:
        yield rsps


@pytest.fixture
def vinyldns_client():
    return VinylDNSClient('http://test.com', 'ok', 'ok')


def test_get_group(mocked_responses, vinyldns_client):
    import json
    g = {'name': 'ok'}
    mocked_responses.add(
        responses.GET, 'http://test.com/groups/123',
        body=json.dumps(g), status=200)
    r = vinyldns_client.get_group('123')
    assert r['name'] == 'ok'
