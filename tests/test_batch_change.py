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
from datetime import datetime, timedelta
from dateutil.tz import tzlocal

import responses
from sampledata import forward_zone
from vinyldns.record import RecordType, AData
from vinyldns.serdes import to_json_string
from vinyldns.batch_change import AddRecordChange, DeleteRecordSetChange, BatchChange, BatchChangeRequest, \
    DeleteRecordSet, AddRecord, BatchChangeSummary, ListBatchChangeSummaries, \
    ValidationError


def check_validation_errors_are_same(a, b):
    assert a.error_type == b.error_type
    assert a.message == b.message


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
    if a.validation_errors:
        for l, r in zip(a.validation_errors, b.validation_errors):
            check_validation_errors_are_same(l, r)


def check_batch_changes_are_same(a, b):
    assert a.user_id == b.user_id
    assert a.user_name == b.user_name
    assert a.comments == b.comments
    assert a.created_timestamp == b.created_timestamp
    assert a.status == b.status
    assert a.id == b.id
    assert a.owner_group_id == b.owner_group_id
    assert a.owner_group_name == b.owner_group_name
    assert a.approval_status == b.approval_status
    assert a.reviewer_id == b.reviewer_id
    assert a.reviewer_user_name == b.reviewer_user_name
    assert a.review_comment == b.review_comment
    assert a.review_timestamp == b.review_timestamp
    assert a.scheduled_time == b.scheduled_time
    for l, r in zip(a.changes, b.changes):
        check_single_changes_are_same(l, r)


def test_create_batch_change(mocked_responses, vinyldns_client):
    ar = AddRecord('foo.baa.com', RecordType.A, 100, AData('1.2.3.4'))
    drs = DeleteRecordSet('baz.bar.com', RecordType.A)
    drs_with_data = DeleteRecordSet('baz-with-data.bar.com', RecordType.A, AData('5.6.7.8'))

    arc = AddRecordChange(forward_zone.id, forward_zone.name, 'foo', 'foo.bar.com', RecordType.A, 200,
                          AData('1.2.3.4'), 'Complete', 'id1', [], 'system-message', 'rchangeid1', 'rsid1')

    drc = DeleteRecordSetChange(forward_zone.id, forward_zone.name, 'baz', 'baz.bar.com', RecordType.A, 'Complete',
                                'id2', [], 'system-message', 'rchangeid2', 'rsid2')

    drc_with_data = DeleteRecordSetChange(forward_zone.id, forward_zone.name, 'baz-with-data', 'baz-with-data.bar.com',
                                          RecordType.A, 'Complete', 'id2', [], 'system-message', 'rchangeid3', 'rsid3',
                                          AData('5.6.7.8'))

    # Python 2/3 compatibility
    try:
        tomorrow = datetime.now().astimezone() + timedelta(1)
    except TypeError:
        tomorrow = datetime.now(tzlocal()).astimezone(tzlocal()) + timedelta(1)

    bc = BatchChange('user-id', 'user-name', datetime.utcnow(), [arc, drc, drc_with_data],
                     'bcid', 'Scheduled', 'PendingReview',
                     comments='batch change test', owner_group_id='owner-group-id',
                     scheduled_time=tomorrow)

    mocked_responses.add(
        responses.POST, 'http://test.com/zones/batchrecordchanges',
        body=to_json_string(bc), status=200
    )

    r = vinyldns_client.create_batch_change(
        BatchChangeRequest(
            changes=[ar, drs, drs_with_data],
            comments='batch change test',
            owner_group_id='owner-group-id',
            scheduled_time=tomorrow
        ))

    check_batch_changes_are_same(r, bc)


def test_get_batch_change(mocked_responses, vinyldns_client):
    arc = AddRecordChange(forward_zone.id, forward_zone.name, 'foo', 'foo.bar.com',
                          RecordType.A, 200, AData('1.2.3.4'), 'Complete', 'id1',
                          [], 'system-message', 'rchangeid1', 'rsid1')

    drc = DeleteRecordSetChange(forward_zone.id, forward_zone.name, 'baz',
                                'baz.bar.com', RecordType.A, 'Complete',
                                'id2', [], 'system-message', 'rchangeid2', 'rsid2')

    drc_with_data = DeleteRecordSetChange(forward_zone.id, forward_zone.name, 'biz',
                                          'biz.bar.com', RecordType.A, 'Complete',
                                          'id3', [], 'system-message', 'rchangeid3', 'rsid3', AData("5.6.7.8"))

    bc = BatchChange('user-id', 'user-name', datetime.utcnow(), [arc, drc, drc_with_data],
                     'bcid', 'Complete', 'AutoApproved',
                     comments='batch change test', owner_group_id='owner-group-id')

    mocked_responses.add(
        responses.GET, 'http://test.com/zones/batchrecordchanges/bcid',
        body=to_json_string(bc), status=200
    )

    r = vinyldns_client.get_batch_change('bcid')

    check_batch_changes_are_same(r, bc)


def test_approve_batch_change(mocked_responses, vinyldns_client):
    arc = AddRecordChange(forward_zone.id, forward_zone.name, 'foo', 'foo.bar.com',
                          RecordType.A, 200, AData('1.2.3.4'), 'PendingReview',
                          'id1', [], 'system-message', 'rchangeid1', 'rsid1')

    drc = DeleteRecordSetChange(forward_zone.id, forward_zone.name, 'baz',
                                'baz.bar.com', RecordType.A, 'PendingReview',
                                'id2', [], 'system-message', 'rchangeid2', 'rsid2')

    bc = BatchChange('user-id', 'user-name', datetime.utcnow(), [arc, drc],
                     'bcid', 'Complete', 'ManuallyApproved',
                     comments='batch change test', owner_group_id='owner-group-id',
                     reviewer_id='admin-id', reviewer_user_name='admin',
                     review_comment='looks good', review_timestamp=datetime.utcnow())

    mocked_responses.add(
        responses.POST, 'http://test.com/zones/batchrecordchanges/bcid/approve',
        body=to_json_string(bc), status=200
    )

    r = vinyldns_client.approve_batch_change('bcid', 'looks good')

    check_batch_changes_are_same(r, bc)


def test_reject_batch_change(mocked_responses, vinyldns_client):
    error_message = "Zone Discovery Failed: zone for \"foo.bar.com\" does not exist in VinylDNS. \
    If zone exists, then it must be connected to in VinylDNS."

    error = ValidationError('ZoneDiscoveryError', error_message)

    arc = AddRecordChange(forward_zone.id, forward_zone.name, 'reject',
                          'reject.bar.com', RecordType.A, 200, AData('1.2.3.4'),
                          'PendingReview', 'id1', [error], 'system-message', 'rchangeid1', 'rsid1')

    drc = DeleteRecordSetChange(forward_zone.id, forward_zone.name, 'reject2',
                                'reject2.bar.com', RecordType.A, 'Complete',
                                'id2', [], 'system-message', 'rchangeid2', 'rsid2')

    bc = BatchChange('user-id', 'user-name', datetime.utcnow(), [arc, drc],
                     'bcid', 'Rejected', 'Rejected',
                     comments='batch change test', owner_group_id='owner-group-id',
                     reviewer_id='admin-id', reviewer_user_name='admin',
                     review_comment='not good', review_timestamp=datetime.utcnow())

    mocked_responses.add(
        responses.POST, 'http://test.com/zones/batchrecordchanges/bcid/reject',
        body=to_json_string(bc), status=200
    )

    r = vinyldns_client.reject_batch_change('bcid', 'not good')

    check_batch_changes_are_same(r, bc)


def test_cancel_batch_change(mocked_responses, vinyldns_client):
    error_message = (
        "Zone Discovery Failed: zone for 'foo.bar.com' does not exist in"
        " VinylDNS. If zone exists, then it must be connected to in VinylDNS."
    )

    error = ValidationError('ZoneDiscoveryError', error_message)

    arc = AddRecordChange(
        forward_zone.id, forward_zone.name, 'cancel', 'cancel.bar.com',
        RecordType.A, 200, AData('1.2.3.4'), 'PendingReview', 'id1',
        [error], 'system-message', 'cchangeid1', 'csid1'
    )

    drc = DeleteRecordSetChange(
        forward_zone.id, forward_zone.name, 'cancel2', 'cancel2.bar.com',
        RecordType.A, 'Complete', 'id2', [], 'system-message', 'cchangeid2',
        'csid2'
    )

    bc = BatchChange(
        'user-id', 'user-name', datetime.utcnow(), [arc, drc], 'bcid',
        'Cancelled', 'Cancelled', owner_group_id='owner-group-id'
    )

    mocked_responses.add(
        responses.POST, 'http://test.com/zones/batchrecordchanges/bcid/cancel',
        body=to_json_string(bc), status=200
    )

    c = vinyldns_client.cancel_batch_change('bcid')

    check_batch_changes_are_same(c, bc)


def test_list_batch_change_summaries(mocked_responses, vinyldns_client):
    bcs1 = BatchChangeSummary('user-id', 'user-name', datetime.utcnow(), 10, 'id1',
                              'Complete', 'AutoApproved', comments='comments',
                              owner_group_id='owner-group-id')
    bcs2 = BatchChangeSummary('user-id2', 'user-name2', datetime.utcnow(), 20,
                              'id2', 'Complete', 'AutoApproved', comments='comments2')
    lbcs = ListBatchChangeSummaries([bcs1, bcs2], 'start', 'next', 50)
    mocked_responses.add(
        responses.GET, 'http://test.com/zones/batchrecordchanges?startFrom=start&maxItems=50',
        body=to_json_string(lbcs), status=200
    )
    r = vinyldns_client.list_batch_change_summaries('start', 50)
    assert r.start_from == lbcs.start_from
    assert r.next_id == lbcs.next_id
    assert r.max_items == lbcs.max_items
    assert r.ignore_access == lbcs.ignore_access
    assert r.approval_status == lbcs.approval_status
    for l, r in zip(r.batch_changes, lbcs.batch_changes):
        assert l.user_id == r.user_id
        assert l.user_name == r.user_name
        assert l.comments == r.comments
        assert l.created_timestamp == r.created_timestamp
        assert l.total_changes == r.total_changes
        assert l.status == r.status
        assert l.id == r.id
        assert l.owner_group_id == r.owner_group_id
