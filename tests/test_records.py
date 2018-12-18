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

import pytest
from vinyldns.record import RecordSet, RecordSetChange, AData, AAAAData, CNAMEData, PTRData, MXData, NSData, SOAData, \
    SRVData, SPFData, \
    SSHFPData, TXTData, RecordType, ListRecordSetsResponse
from vinyldns.serdes import to_json_string, from_json_string

from vinyldns.zone import ACLRule, AccessLevel, Zone, ZoneACL, ZoneConnection

record_sets = [
    RecordSet('zoneid', 'a-test', RecordType.A, 200, records=[AData('1.2.3.4')]),
    RecordSet('zoneid', 'aaaa-test', RecordType.AAAA, 200, records=[AAAAData('1:2:3:4:5:6:7:8')]),
    RecordSet('zoneid', 'cname-test', RecordType.CNAME, 200, records=[CNAMEData('cname')]),
    RecordSet('0.168.192.in-addr.arpa', '30', RecordType.PTR, 200, records=[PTRData('alias')]),
    RecordSet('zoneid', 'srv-test', RecordType.SRV, 200, records=[SRVData(1, 2, 3, 'target')]),
    RecordSet('zoneid', 'mx-test', RecordType.MX, 200, records=[MXData(1, 'mail')]),
    RecordSet('zoneid', 'ns-test', RecordType.NS, 200, records=[NSData('ns1.foo.bar')]),
    RecordSet('zoneid', 'soa-test', RecordType.SOA, 200, records=[SOAData('mname', 'rname', 100, 200, 300, 400, 500)]),
    RecordSet('zoneid', 'spf-test', RecordType.SPF, 200, records=[SPFData('some-spf')]),
    RecordSet('zoneid', 'txt-test', RecordType.TXT, 200, records=[TXTData('some-text')]),
    RecordSet('zoneid', 'sshfp-test', RecordType.SSHFP, 200, records=[SSHFPData('algorithm', 'type', 'fingerprint')]),
]


def get_rs_type(rs):
    return rs.type


@pytest.fixture(scope="module", params=record_sets, ids=get_rs_type)
def rs_fixture(request):
    return request.param


def check_record_sets_are_equal(a, b):
    assert a.zone_id == b.zone_id
    assert a.type == b.type
    assert a.ttl == b.ttl
    assert a.name == b.name
    assert all([l.__dict__ == r.__dict__ for l, r in zip(a.records, b.records)])


def test_record_set_serdes(rs_fixture):
    rs = rs_fixture
    s = to_json_string(rs)
    r = from_json_string(s, RecordSet.from_dict)
    check_record_sets_are_equal(r, rs)


def test_record_set_changes_serdes(rs_fixture):
    acl_rule = ACLRule(AccessLevel.Read, 'my desc', 'foo_user', None, '*', ['A', 'AAAA'])
    conn = ZoneConnection(name='fooConn', key_name='fooKeyName', key='fooKey', primary_server='fooPS')
    zone = Zone(id='foo', name='bar', email='test@test.com', admin_group_id='foo', connection=conn,
                transfer_connection=conn, acl=ZoneACL([acl_rule]))
    a = RecordSetChange(zone=zone, record_set=rs_fixture, user_id='test-user', change_type='Create', status='Pending',
                        created='some-date', system_message=None, updates=rs_fixture, id='some-id',
                        user_name='some-username')
    s = to_json_string(a)
    b = from_json_string(s, RecordSetChange.from_dict)

    assert a.user_id == b.user_id
    assert a.change_type == b.change_type
    assert a.status == b.status
    assert a.created == b.created
    assert a.system_message == b.system_message
    assert a.id == b.id
    assert a.user_name == b.user_name
    check_record_sets_are_equal(a.record_set, b.record_set)
    check_record_sets_are_equal(a.updates, b.updates)
    assert a.zone.id == b.zone.id


def test_list_record_set_response_serdes():
    a = ListRecordSetsResponse(record_sets=record_sets, start_from='some-start', next_id='next', max_items=100, record_name_filter='foo*')
    s = to_json_string(a)
    b = from_json_string(s, ListRecordSetsResponse.from_dict)

    assert a.start_from == b.start_from
    assert a.next_id == b.next_id
    assert a.max_items == b.max_items
    assert a.record_name_filter == b.record_name_filter
    assert len(a.record_sets) == len(b.record_sets)
    for l, r in zip(a.record_sets, b.record_sets):
        check_record_sets_are_equal(l, r)
