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
import datetime

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
        assert all([l.__dict__ == r.__dict__ for l, r in zip(a.members, b.members)])
        assert all([l.__dict__ == r.__dict__ for l, r in zip(a.admins, b.admins)])


def test_create_group(mocked_responses, vinyldns_client):
    mocked_responses.add(
        responses.POST, 'http://test.com/groups',
        body=to_json_string(sample_group), status=200)
    r = vinyldns_client.create_group(sample_group)
    check_groups_are_same(sample_group, r)


def test_update_group(mocked_responses, vinyldns_client):
    mocked_responses.add(
        responses.PUT, 'http://test.com/groups/' + sample_group.id,
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

    for l, r in zip(sample_list_groups.groups, r.groups):
        check_groups_are_same(l, r)


def test_list_all_my_groups(mocked_responses, vinyldns_client):
    sample_list_groups1 = ListGroupsResponse([sample_group], 1, '*', 'start-from', 'next-id')

    # Set next id to None to indicate end of list
    sample_list_groups2 = ListGroupsResponse([sample_group2], 1, '*', 'start-from', next_id=None)
    mocked_responses.add(
        responses.GET, 'http://test.com/groups?groupNameFilter=*',
        body=to_json_string(sample_list_groups1), status=200)

    # list all puts the next id from the first response into the startFrom for the next request
    mocked_responses.add(
        responses.GET, 'http://test.com/groups?groupNameFilter=*&startFrom=next-id',
        body=to_json_string(sample_list_groups2), status=200)
    r = vinyldns_client.list_all_my_groups('*')

    assert r.start_from is None
    assert r.next_id is None
    assert sample_list_groups1.group_name_filter == r.group_name_filter

    for l, r in zip([sample_group, sample_group2], r.groups):
        check_groups_are_same(l, r)


def test_list_members(mocked_responses, vinyldns_client):
    member1 = Member('some-id', 'user-name', 'first', 'last', 'test@test.com', datetime.datetime.utcnow(), False)
    member2 = Member('some-id2', 'user-name2', 'first2', 'last2', 'test2@test.com', datetime.datetime.utcnow(), False)
    lmr = ListMembersResponse([member1, member2], start_from='start', next_id='next', max_items=100)
    mocked_responses.add(
        responses.GET, 'http://test.com/groups/foo/members?startFrom=start&maxItems=100',
        body=to_json_string(lmr), status=200
    )
    r = vinyldns_client.list_members_group('foo', 'start', 100)
    r.start_from = lmr.start_from
    r.next_id = lmr.next_id
    r.max_items = lmr.max_items

    for l, r in zip(lmr.members, r.members):
        assert l.id == r.id
        assert l.user_name == r.user_name
        assert l.first_name == r.first_name
        assert l.last_name == r.last_name
        assert l.email == r.email
        assert l.created == r.created
        assert l.is_admin == r.is_admin


def test_list_group_admins(mocked_responses, vinyldns_client):
    user1 = User('id', 'test200', 'Bobby', 'Bonilla', 'bob@bob.com', datetime.datetime.utcnow())
    user2 = User('id2', 'test2002', 'Frank', 'Bonilla', 'frank@bob.com', datetime.datetime.utcnow())
    lar = ListAdminsResponse([user1, user2])
    mocked_responses.add(
        responses.GET, 'http://test.com/groups/foo/admins',
        body=to_json_string(lar), status=200
    )
    r = vinyldns_client.list_group_admins('foo')
    for l, r in zip(lar.admins, r.admins):
        assert l.id == r.id
        assert l.user_name == r.user_name
        assert l.first_name == r.first_name
        assert l.last_name == r.last_name
        assert l.email == r.email
        assert l.created == r.created
        assert l.lock_status == r.lock_status


def test_list_group_changes(mocked_responses, vinyldns_client):
    change1 = GroupChange(sample_group, 'Create', 'user', None, 'id', datetime.datetime.utcnow())
    change2 = GroupChange(sample_group2, 'Update', 'user', sample_group, 'id2', datetime.datetime.utcnow())
    lgcr = ListGroupChangesResponse([change1, change2], 'start', 'next', 100)
    mocked_responses.add(
        responses.GET, 'http://test.com/groups/foo/activity?startFrom=start&maxItems=100',
        body=to_json_string(lgcr), status=200
    )
    r = vinyldns_client.list_group_changes('foo', 'start', 100)
    assert r.next_id == lgcr.next_id
    assert r.start_from == lgcr.start_from
    assert r.max_items == lgcr.max_items
    for l, r in zip(lgcr.changes, r.changes):
        assert l.change_type == r.change_type
        assert l.user_id == r.user_id
        assert l.id == r.id
        assert l.created == r.created
        check_groups_are_same(l.new_group, r.new_group)
        check_groups_are_same(l.old_group, r.old_group)


def test_group_serdes():
    r = from_json_string(to_json_string(sample_group), Group.from_dict)
    check_groups_are_same(sample_group, r)
