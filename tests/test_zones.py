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
from vinyldns.record import RecordSet, AData, AAAAData, CNAMEData, PTRData, MXData, NSData, SOAData, SRVData, SPFData, \
    SSHFPData, TXTData, RecordType
from vinyldns.serdes import to_json_string, from_json_string
from vinyldns.zone import AccessLevel, ACLRule, ZoneConnection, ZoneACL, Zone


def test_zone_serdes():
    acl_rule = ACLRule(AccessLevel.Read, 'my desc', 'foo_user', None, '*', ['A', 'AAAA'])
    conn = ZoneConnection(name='fooConn', key_name='fooKeyName', key='fooKey', primary_server='fooPS')
    zone = Zone(id='foo', name='bar', email='test@test.com', admin_group_id='foo', connection=conn,
                transfer_connection=conn, acl=ZoneACL([acl_rule]))
    s = to_json_string(zone)
    print(json.dumps(s, indent=4))
    z = from_json_string(s, Zone.from_dict)

    assert z.name == zone.name
    assert z.connection.primary_server == zone.connection.primary_server
    assert all([a.__dict__ == b.__dict__ for a, b in zip(z.acl.rules, zone.acl.rules)])

