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

from datetime import datetime, UTC

import responses

from vinyldns.membership import Group, GroupChange, ListAdminsResponse, ListGroupsResponse, ListGroupChangesResponse, \
    ListMembersResponse, Member, User
from vinyldns.serdes import to_json_string, from_json_string
from sampledata import sample_group, sample_group2


def check_groups_are_same(a, b):
    if a is None and b is None:
        assert a == b
    else:
        assert a.id == b.id
        assert a.description == b.description
        assert a.created == b.created
        assert a.name == b.name
        assert a.email == b.email
        for left_member, right_member in zip(a.members, b.members):
            assert left_member.__dict__ == right_member.__dict__
        for left_admin, right_admin in zip(a.admins, b.admins):
            assert left_admin.__dict__ == right_admin.__dict__


def test_create_group(mocked_responses, vinyldns_client):
    mocked_responses.add(
        responses.POST, 'http://test.com/groups',
        body=to_json_string(sample_group), status=200)
    r = vinyldns_client.create_group(sample_group)
    check_groups_are_same(sample_group, r)


def test_update_group(mocked_responses, vinyldns_client):
    mocked_responses.add(
        responses.PUT, f'http://test.com/groups/{sample_group.id}',
        body=to_json_string(sample_group), status=200)
    r = vinyldns_client.update_group(sample_group)
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

    for left_group, right_group in zip(sample_list_groups.groups, r.groups):
        check_groups_are_same(left_group, right_group)


def test_list_all_my_groups(mocked_responses, vinyldns_client):
    sample_list_groups1 = ListGroupsResponse([sample_group], 1, '*', 'start-from', 'next-id')
    sample_list_groups2 = ListGroupsResponse([sample_group2], 1, '*', 'start-from', next_id=None)
    mocked_responses.add(
        responses.GET, 'http://test.com/groups?groupNameFilter=*',
        body=to_json_string(sample_list_groups1), status=200)
    mocked_responses.add(
        responses.GET, 'http://test.com/groups?groupNameFilter=*&startFrom=next-id',
        body=to_json_string(sample_list_groups2), status=200)

    r = vinyldns_client.list_all_my_groups('*')
    assert r.start_from is None
    assert r.next_id is None
    assert sample_list_groups1.group_name_filter == r.group_name_filter

    for left_group, right_group in zip([sample_group, sample_group2], r.groups):
        check_groups_are_same(left_group, right_group)


def test_list_members(mocked_responses, vinyldns_client):
    member1 = Member('some-id', 'user-name', 'first', 'last', 'test@test.com', datetime.now(UTC), False)
    member2 = Member('some-id2', 'user-name2', 'first2', 'last2', 'test2@test.com', datetime.now(UTC), False)
    list_members_response = ListMembersResponse([member1, member2], start_from='start', next_id='next', max_items=100)
    mocked_responses.add(
        responses.GET, 'http://test.com/groups/foo/members?startFrom=start&maxItems=100',
        body=to_json_string(list_members_response), status=200
    )

    r = vinyldns_client.list_members_group('foo', 'start', 100)
    r.start_from = list_members_response.start_from
    r.next_id = list_members_response.next_id
    r.max_items = list_members_response.max_items

    for left_member, right_member in zip(list_members_response.members, r.members):
        assert left_member.id == right_member.id
        assert left_member.user_name == right_member.user_name
        assert left_member.first_name == right_member.first_name
        assert left_member.last_name == right_member.last_name
        assert left_member.email == right_member.email
        assert left_member.created == right_member.created
        assert left_member.is_admin == right_member.is_admin


def test_list_group_admins(mocked_responses, vinyldns_client):
    user1 = User('id', 'test200', 'Bobby', 'Bonilla', 'bob@bob.com', datetime.now(UTC))
    user2 = User('id2', 'test2002', 'Frank', 'Bonilla', 'frank@bob.com', datetime.now(UTC))
    list_admins_response = ListAdminsResponse([user1, user2])
    mocked_responses.add(
        responses.GET, 'http://test.com/groups/foo/admins',
        body=to_json_string(list_admins_response), status=200
    )

    r = vinyldns_client.list_group_admins('foo')
    for left_user, right_user in zip(list_admins_response.admins, r.admins):
        assert left_user.id == right_user.id
        assert left_user.user_name == right_user.user_name
        assert left_user.first_name == right_user.first_name
        assert left_user.last_name == right_user.last_name
        assert left_user.email == right_user.email
        assert left_user.created == right_user.created
        assert left_user.lock_status == right_user.lock_status


def test_list_group_changes(mocked_responses, vinyldns_client):
    change1 = GroupChange(sample_group, 'Create', 'user', None, 'id', datetime.now(UTC))
    change2 = GroupChange(sample_group2, 'Update', 'user', sample_group, 'id2', datetime.now(UTC))
    list_group_changes_response = ListGroupChangesResponse([change1, change2], 'start', 'next', 100)
    mocked_responses.add(
        responses.GET, 'http://test.com/groups/foo/activity?startFrom=start&maxItems=100',
        body=to_json_string(list_group_changes_response), status=200
    )

    r = vinyldns_client.list_group_changes('foo', 'start', 100)
    assert r.next_id == list_group_changes_response.next_id
    assert r.start_from == list_group_changes_response.start_from
    assert r.max_items == list_group_changes_response.max_items

    for left_change, right_change in zip(list_group_changes_response.changes, r.changes):
        assert left_change.change_type == right_change.change_type
        assert left_change.user_id == right_change.user_id
        assert left_change.id == right_change.id
        assert left_change.created == right_change.created
        check_groups_are_same(left_change.new_group, right_change.new_group)
        check_groups_are_same(left_change.old_group, right_change.old_group)


def test_group_serdes():
    r = from_json_string(to_json_string(sample_group), Group.from_dict)
    check_groups_are_same(sample_group, r)
