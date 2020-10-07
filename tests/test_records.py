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
import copy

import responses
from sampledata import record_sets, record_set_values, gen_rs_change, forward_zone
from vinyldns.record import RecordSet, RecordSetChange, ListRecordSetsResponse, ListRecordSetChangesResponse
from vinyldns.serdes import to_json_string, from_json_string


def check_record_sets_are_equal(a, b):
    if a is None:
        assert a == b
    else:
        assert a.zone_id == b.zone_id
        assert a.type == b.type
        assert a.ttl == b.ttl
        assert a.name == b.name
        assert a.owner_group_id == b.owner_group_id
        assert all([l.__dict__ == r.__dict__ for l, r in zip(a.records, b.records)])


def check_record_set_changes_are_equal(a, b):
    if a is None:
        assert a == b
    else:
        assert a.user_id == b.user_id
        assert a.change_type == b.change_type
        assert a.status == b.status
        assert a.created == b.created
        assert a.system_message == b.system_message
        assert a.id == b.id
        assert a.user_name == b.user_name
        assert a.zone.id == b.zone.id
        check_record_sets_are_equal(a.record_set, b.record_set)
        check_record_sets_are_equal(a.updates, b.updates)


def test_create_record_set(record_set, mocked_responses, vinyldns_client):
    change = gen_rs_change(record_set)
    mocked_responses.add(
        responses.POST, 'http://test.com/zones/{0}/recordsets'.format(record_set.zone_id),
        body=to_json_string(change), status=200
    )
    r = vinyldns_client.create_record_set(record_set)
    check_record_set_changes_are_equal(change, r)
    mocked_responses.reset()


def test_update_record_set(record_set, mocked_responses, vinyldns_client):
    rs = copy.deepcopy(record_set)
    rs.id = rs.name + 'id'
    change = gen_rs_change(rs)
    mocked_responses.add(
        responses.PUT, 'http://test.com/zones/{0}/recordsets/{1}'.format(rs.zone_id, rs.id),
        body=to_json_string(change), status=200
    )
    r = vinyldns_client.update_record_set(rs)
    check_record_set_changes_are_equal(change, r)
    mocked_responses.reset()


def test_delete_record_set(record_set, mocked_responses, vinyldns_client):
    rs = copy.deepcopy(record_set)
    rs.id = rs.name + 'id'
    change = gen_rs_change(rs)
    mocked_responses.add(
        responses.DELETE, 'http://test.com/zones/{0}/recordsets/{1}'.format(rs.zone_id, rs.id),
        body=to_json_string(change), status=200
    )
    r = vinyldns_client.delete_record_set(rs.zone_id, rs.id)
    check_record_set_changes_are_equal(change, r)
    mocked_responses.reset()


def test_get_record_set(record_set, mocked_responses, vinyldns_client):
    rs = copy.deepcopy(record_set)
    rs.id = rs.name + 'id'
    response = {'recordSet': rs}
    mocked_responses.add(
        responses.GET, 'http://test.com/zones/{0}/recordsets/{1}'.format(rs.zone_id, rs.id),
        body=to_json_string(response), status=200
    )
    r = vinyldns_client.get_record_set(rs.zone_id, rs.id)
    check_record_sets_are_equal(rs, r)
    mocked_responses.reset()


def test_list_record_sets(mocked_responses, vinyldns_client):
    lrr = ListRecordSetsResponse(record_set_values, 'start', 'next', 100, '*')
    mocked_responses.add(
        responses.GET,
        'http://test.com/zones/{0}/recordsets?startFrom=start&maxItems=100&recordNameFilter=*'.format(forward_zone.id),
        body=to_json_string(lrr), status=200
    )
    r = vinyldns_client.list_record_sets(forward_zone.id, 'start', 100, '*')
    assert r.start_from == lrr.start_from
    assert r.next_id == lrr.next_id
    assert r.record_name_filter == lrr.record_name_filter
    assert r.max_items == lrr.max_items
    for l, r in zip(r.record_sets, lrr.record_sets):
        check_record_sets_are_equal(l, r)


def test_search_record_sets(mocked_responses, vinyldns_client):
    lrr = ListRecordSetsResponse(record_set_values, 'start', 'next', 100, '*')
    all_record_types = list(record_sets.keys())
    record_type_filter = ''
    for record_type in all_record_types:
        record_type_filter += '&recordTypeFilter[]={0}'.format(record_type)
    mocked_responses.add(
        responses.GET,
        'http://test.com/recordsets?startFrom=start&maxItems=100&recordNameFilter=*' +
        record_type_filter + '&recordOwnerGroupFilter=owner-group-id&nameSort=DESC',
        body=to_json_string(lrr), status=200
    )
    r = vinyldns_client.search_record_sets('start', 100, '*', all_record_types, 'owner-group-id', 'DESC')
    assert r.start_from == lrr.start_from
    assert r.next_id == lrr.next_id
    assert r.record_name_filter == lrr.record_name_filter
    assert r.max_items == lrr.max_items
    for l, r in zip(r.record_sets, lrr.record_sets):
        check_record_sets_are_equal(l, r)


def test_get_record_set_change(record_set, mocked_responses, vinyldns_client):
    change = gen_rs_change(record_set)
    mocked_responses.add(
        responses.GET,
        'http://test.com/zones/{0}/recordsets/{1}/changes/{2}'.format(record_set.zone_id, record_set.id, change.id),
        body=to_json_string(change), status=200
    )
    r = vinyldns_client.get_record_set_change(record_set.zone_id, record_set.id, change.id)
    check_record_set_changes_are_equal(r, change)


def test_list_record_set_changes(mocked_responses, vinyldns_client):
    changes = [gen_rs_change(c) for c in record_set_values]
    lrscr = ListRecordSetChangesResponse(forward_zone.id, changes, 'next', 'start', 100)
    mocked_responses.add(responses.GET,
                         'http://test.com/zones/{0}/recordsetchanges?startFrom=start&maxItems=100'.format(
                             forward_zone.id), body=to_json_string(lrscr), status=200)
    r = vinyldns_client.list_record_set_changes(forward_zone.id, 'start', 100)
    r.start_from = lrscr.start_from
    r.next_id = lrscr.next_id
    r.max_items = lrscr.max_items
    r.zone_id = lrscr.zone_id
    for l, r in zip(r.record_set_changes, lrscr.record_set_changes):
        check_record_set_changes_are_equal(l, r)


def test_record_set_serdes(record_set):
    rs = record_set
    s = to_json_string(rs)
    r = from_json_string(s, RecordSet.from_dict)
    check_record_sets_are_equal(r, rs)


def test_record_set_changes_serdes(record_set):
    a = gen_rs_change(record_set)
    s = to_json_string(a)
    b = from_json_string(s, RecordSetChange.from_dict)

    assert a.user_id == b.user_id
    assert a.change_type == b.change_type
    assert a.status == b.status
    assert a.created == b.created
    assert a.system_message == b.system_message
    assert a.id == b.id
    assert a.user_name == b.user_name
    assert a.zone.id == b.zone.id
    check_record_sets_are_equal(a.record_set, b.record_set)
    check_record_sets_are_equal(a.updates, b.updates)


def test_list_record_set_response_serdes():
    a = ListRecordSetsResponse(record_sets=record_set_values, start_from='some-start', next_id='next',
                               max_items=100,
                               record_name_filter='foo*')
    s = to_json_string(a)
    b = from_json_string(s, ListRecordSetsResponse.from_dict)

    assert a.start_from == b.start_from
    assert a.next_id == b.next_id
    assert a.max_items == b.max_items
    assert a.record_name_filter == b.record_name_filter
    assert len(a.record_sets) == len(b.record_sets)
    for l, r in zip(a.record_sets, b.record_sets):
        check_record_sets_are_equal(l, r)
