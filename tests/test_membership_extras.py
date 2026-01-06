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

import datetime

import responses

from sampledata import sample_group
from vinyldns.membership import GroupChange
from vinyldns.serdes import to_json_string


def test_get_group_change(mocked_responses, vinyldns_client):
    change = GroupChange(sample_group, 'Update', 'user-id', sample_group, 'change-id', datetime.datetime.utcnow(),
                         user_name='user', group_change_message='updated')
    mocked_responses.add(
        responses.GET, 'http://test.com/groups/change/change-id',
        body=to_json_string(change), status=200)

    resp = vinyldns_client.get_group_change('change-id')
    assert resp.id == 'change-id'
    assert resp.user_name == 'user'
    assert resp.group_change_message == 'updated'


def test_list_group_valid_domains(mocked_responses, vinyldns_client):
    mocked_responses.add(
        responses.GET, 'http://test.com/groups/valid/domains',
        body=to_json_string(['example.com', 'test.com']), status=200)

    resp = vinyldns_client.list_group_valid_domains()
    assert resp == ['example.com', 'test.com']
