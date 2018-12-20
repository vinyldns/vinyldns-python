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

import responses

from vinyldns.membership import Group, ListGroupsResponse
from vinyldns.serdes import to_json_string, from_json_string
from sampledata import sample_group, sample_group2


def check_groups_are_same(a, b):
    assert a.id == b.id
    assert a.description == b.description
    assert a.created == b.created
    assert a.name == b.name
    assert all([l.__dict__ == r.__dict__ for l, r in zip(a.members, b.members)])
    assert all([l.__dict__ == r.__dict__ for l, r in zip(a.admins, b.admins)])


def test_create_groups(mocked_responses, vinyldns_client):
    mocked_responses.add(
        responses.POST, 'http://test.com/groups',
        body=to_json_string(sample_group), status=200)
    r = vinyldns_client.create_group(sample_group)
    check_groups_are_same(sample_group, r)


def test_get_group(mocked_responses, vinyldns_client):
    mocked_responses.add(
        responses.GET, 'http://test.com/groups/123',
        body=to_json_string(sample_group), status=200)
    r = vinyldns_client.get_group('123')
    check_groups_are_same(sample_group, r)


def test_delete_group(mocked_responses, vinyldns_client):
    mocked_responses.add(
        responses.DELETE, 'http://test.com/groups/123',
        body=to_json_string(sample_group), status=200)
    r = vinyldns_client.delete_group('123')
    check_groups_are_same(sample_group, r)


def test_list_my_groups(mocked_responses, vinyldns_client):
    sample_list_groups = ListGroupsResponse([sample_group, sample_group2], 5, '*', 'start-from', 'next-id')
    mocked_responses.add(
        responses.GET, 'http://test.com/groups?groupNameFilter=*&startFrom=start-from&maxItems=5',
        body=to_json_string(sample_list_groups), status=200)
    r = vinyldns_client.list_my_groups('*', 'start-from', 5)
    assert sample_list_groups.start_from == r.start_from
    assert sample_list_groups.group_name_filter == r.group_name_filter
    assert sample_list_groups.next_id == r.next_id

    print(to_json_string(r.groups))
    print(to_json_string(sample_list_groups.groups))
    for l, r in zip(sample_list_groups.groups, r.groups):
        check_groups_are_same(l, r)


def test_group_serdes():
    r = from_json_string(to_json_string(sample_group), Group.from_dict)
    check_groups_are_same(sample_group, r)

