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

from tests.sampledata import record_set_values, gen_rs_change
from src.vinyldns.record import RecordSet, RecordSetChange, ListRecordSetsResponse
from src.vinyldns.serdes import to_json_string, from_json_string


def check_record_sets_are_equal(a, b):
    assert a.zone_id == b.zone_id
    assert a.type == b.type
    assert a.ttl == b.ttl
    assert a.name == b.name
    assert all([l.__dict__ == r.__dict__ for l, r in zip(a.records, b.records)])


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
    a = ListRecordSetsResponse(record_sets=record_set_values, start_from='some-start', next_id='next', max_items=100,
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
