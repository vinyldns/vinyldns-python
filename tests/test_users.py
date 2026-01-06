# Copyright 2026 Comcast Cable Communications Management, LLC
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

from vinyldns.serdes import to_json_string


def test_get_user(mocked_responses, vinyldns_client):
    body = {
        'id': 'user-id',
        'userName': 'user',
        'groupId': [{'id': 'group-1'}, {'id': 'group-2'}],
        'lockStatus': 'Unlocked'
    }
    mocked_responses.add(
        responses.GET, 'http://test.com/users/user-id',
        body=to_json_string(body), status=200)

    user = vinyldns_client.get_user('user-id')
    assert user.id == 'user-id'
    assert user.user_name == 'user'
    assert len(user.group_ids) == 2


def test_lock_user(mocked_responses, vinyldns_client):
    body = {
        'id': 'user-id',
        'userName': 'user',
        'groupId': [{'id': 'group-1'}],
        'lockStatus': 'Locked'
    }
    mocked_responses.add(
        responses.PUT, 'http://test.com/users/user-id/lock',
        body=to_json_string(body), status=200)

    user = vinyldns_client.lock_user('user-id')
    assert user.lock_status == 'Locked'


def test_unlock_user(mocked_responses, vinyldns_client):
    body = {
        'id': 'user-id',
        'userName': 'user',
        'groupId': [{'id': 'group-1'}],
        'lockStatus': 'Unlocked'
    }
    mocked_responses.add(
        responses.PUT, 'http://test.com/users/user-id/unlock',
        body=to_json_string(body), status=200)

    user = vinyldns_client.unlock_user('user-id')
    assert user.lock_status == 'Unlocked'
