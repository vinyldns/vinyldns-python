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

import responses
from sampledata import record_set_values, gen_rs_change, forward_zone
from vinyldns.record import RecordSet, RecordSetChange, RecordType, ListRecordSetsResponse, ListRecordSetChangesResponse
from vinyldns.serdes import to_json_string, from_json_string
from vinyldns.batch_change import AddRecordChange, DeleteRecordSetChange, BatchChange, BatchChangeRequest, \
    DeleteRecordSet, AddRecord


def check_single_changes_are_same(a, b):
    assert a.zone_id == b.zone_id
    assert a.zone_name == b.zone_name
    assert a.record_name == b.record_name
    assert a.input_name == b.input_name
    assert a.type == b.type
    assert a.status == b.status
    assert a.id == b.id
    assert a.system_message == b.system_message
    assert a.record_change_id == b.record_change_id
    assert a.record_set_id == b.record_set_id
    if a.type == 'Add':
        assert a.ttl == b.ttl
        assert a.record_data == b.record_data


def test_create_batch_change(mocked_responses, vinyldns_client):
    ar = AddRecord('foo.bar.com', RecordType.A, 100, '1.2.3.4')
    drs = DeleteRecordSet('baz.bar.com', RecordType.A)

    arc = AddRecordChange(forward_zone.id, forward_zone.name, 'foo', 'foo.bar.com', RecordType.A, '1.2.3.4', 'Complete',
                          'id1', 'system-message', 'rchangeid1', 'rsid1')
    drc = DeleteRecordSetChange(forward_zone.id, forward_zone.name, 'baz', 'baz.bar.com', RecordType.A, 'Complete',
                                'id2', 'system-message', 'rchangeid2', 'rsid2')
    bc = BatchChange('user-id', 'user-name', 'batch change test', datetime.utcnow(), [arc, drc], 'bcid')
    mocked_responses.add(
        responses.POST, 'http://test.com/zones/batchrecordchanges',
        body=to_json_string(bc), status=200
    )
    r = vinyldns_client.create_batch_change(
        BatchChangeRequest(
            changes=[ar, drs],
            comments='batch change test'
        ))

    assert r.user_id == bc.user_id
    assert r.user_name == bc.user_name
    assert r.comments == bc.comments
    assert r.created_timestamp == bc.created_timestamp
    assert r.id == bc.id
    for l, r in zip(r.changes, bc.changes):
        check_single_changes_are_same(l, r)


def test_get_batch_change(mocked_responses, vinyldns_client):
    arc = AddRecordChange(forward_zone.id, forward_zone.name, 'foo', 'foo.bar.com', RecordType.A, '1.2.3.4', 'Complete',
                          'id1', 'system-message', 'rchangeid1', 'rsid1')
    drc = DeleteRecordSetChange(forward_zone.id, forward_zone.name, 'baz', 'baz.bar.com', RecordType.A, 'Complete',
                            'id2', 'system-message', 'rchangeid2', 'rsid2')
    bc = BatchChange('user-id', 'user-name', 'batch change test', datetime.utcnow(), [arc, drc], 'bcid')
    mocked_responses.add(
        responses.GET, 'http://test.com/zones/batchrecordchanges/bcid',
        body=to_json_string(bc), status=200
    )
    r = vinyldns_client.get_batch_change('bcid')
    assert r.user_id == bc.user_id
    assert r.user_name == bc.user_name
    assert r.comments == bc.comments
    assert r.created_timestamp == bc.created_timestamp
    assert r.id == bc.id
    for l, r in zip(r.changes, bc.changes):
        check_single_changes_are_same(l, r)
