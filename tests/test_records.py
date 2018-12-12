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
from vinyldns.record import RecordSet, AData, AAAAData, CNAMEData, PTRData, MXData, NSData, SOAData, SRVData, SPFData, \
    SSHFPData, TXTData, RecordType


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


def test_record_set_serdes(rs_fixture):
    rs = RecordSet('zoneid', 'a-test', RecordType.A, 200, records=[AData('1.2.3.4')])
    s = to_json_string(rs)
    r = from_json_string(s, RecordSet.from_dict)

    assert r.zone_id == rs.zone_id
    assert r.type == rs.type
    assert r.ttl == rs.ttl
    assert r.name == rs.name
    assert all([a.__dict__ == b.__dict__ for a, b in zip(r.records, rs.records)])
