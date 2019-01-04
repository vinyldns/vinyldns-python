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
from datetime import datetime

from vinyldns.record import RecordSet, RecordSetChange, AData, AAAAData, CNAMEData, PTRData, MXData, NSData, SOAData, \
    SRVData, SPFData, SSHFPData, TXTData, RecordType
from vinyldns.zone import ACLRule, AccessLevel, Zone, ZoneACL, ZoneChange, ZoneConnection

from vinyldns.membership import Group, User

acl_rule = ACLRule(AccessLevel.Read, 'my desc', 'foo_user', None, '*', ['A', 'AAAA'])
conn = ZoneConnection(name='fooConn', key_name='fooKeyName', key='fooKey', primary_server='fooPS')
forward_zone = Zone(id='foo', name='bar', email='test@test.com', admin_group_id='foo', connection=conn,
                    transfer_connection=conn, acl=ZoneACL([acl_rule]))
ip4_zone = Zone(id='ip4', name='0.168.192.in-addr.arpa', email='test@test.com', admin_group_id='foo', connection=conn,
                transfer_connection=conn, acl=ZoneACL([acl_rule]))
ip6_zone = Zone(id='ip6', name='1.9.e.f.c.c.7.2.9.6.d.f.ip6.arpa', email='test@test.com', admin_group_id='foo',
                connection=conn, transfer_connection=conn, acl=ZoneACL([acl_rule]))

sample_zone_change = ZoneChange(zone=forward_zone, user_id='some-user', change_type='Create', status='Pending',
                                created=datetime.utcnow(), system_message=None, id='zone-change-id')

record_sets = {
    RecordType.A: RecordSet(forward_zone.id, 'a-test', RecordType.A, 200, records=[AData('1.2.3.4')]),
    RecordType.AAAA: RecordSet(forward_zone.id, 'aaaa-test', RecordType.AAAA, 200,
                               records=[AAAAData('1:2:3:4:5:6:7:8')]),
    RecordType.CNAME: RecordSet(forward_zone.id, 'cname-test', RecordType.CNAME, 200, records=[CNAMEData('cname')]),
    RecordType.PTR: RecordSet('0.168.192.in-addr.arpa', '30', RecordType.PTR, 200, records=[PTRData('alias')]),
    RecordType.SRV: RecordSet(forward_zone.id, 'srv-test', RecordType.SRV, 200, records=[SRVData(1, 2, 3, 'target')]),
    RecordType.MX: RecordSet(forward_zone.id, 'mx-test', RecordType.MX, 200, records=[MXData(1, 'mail')]),
    RecordType.NS: RecordSet(forward_zone.id, 'ns-test', RecordType.NS, 200, records=[NSData('ns1.foo.bar')]),
    RecordType.SOA: RecordSet(forward_zone.id, 'soa-test', RecordType.SOA, 200,
                              records=[SOAData('mname', 'rname', 100, 200, 300, 400, 500)]),
    RecordType.SPF: RecordSet(forward_zone.id, 'spf-test', RecordType.SPF, 200, records=[SPFData('some-spf')]),
    RecordType.TXT: RecordSet(forward_zone.id, 'txt-test', RecordType.TXT, 200, records=[TXTData('some-text')]),
    RecordType.SSHFP: RecordSet(forward_zone.id, 'sshfp-test', RecordType.SSHFP, 200,
                                records=[SSHFPData('algorithm', 'type', 'fingerprint')]),
}

record_set_values = record_sets.values()

sample_user = User('id', 'test200', 'Bobby', 'Bonilla', 'bob@bob.com', datetime.utcnow())
sample_group = Group('ok', 'test@test.com', 'description', datetime.utcnow(), members=[sample_user],
                     admins=[sample_user], id='sample-group')
sample_group2 = Group('ok2', 'test@test.com', 'description', datetime.utcnow(), members=[sample_user],
                      admins=[sample_user], id='sample-group2')


def gen_rs_change(record_set):
    return RecordSetChange(zone=forward_zone, record_set=record_set, user_id='test-user',
                           change_type='Create', status='Pending', created=datetime.utcnow(), system_message=None,
                           updates=record_set, id='some-id', user_name='some-username')
