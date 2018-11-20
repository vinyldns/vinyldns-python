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
import responses
import pytest
from vinyldns.client import VinylDNSClient
from vinyldns.zone import *
from vinyldns.serdes import *


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


def test_zone():
    acl_rule = ACLRule('Read', 'my desc', 'foo_user', None, '*', ['A', 'AAAA'])
    conn = ZoneConnection(name='fooConn', key_name='fooKeyName', key='fooKey', primary_server='fooPS')
    zone = Zone(id='foo', name='bar', email='test@test.com', admin_group_id='foo', connection=conn,
                transfer_connection=conn, acl=ZoneACL([acl_rule]))
    s = to_json_string(zone)
    print(json.dumps(s, indent=4))
    z = from_json_string(s, Zone.from_dict)

    assert z.name == zone.name
    assert z.connection.primary_server == zone.connection.primary_server
    assert z.acl.rules[0].access_level == acl_rule.access_level
