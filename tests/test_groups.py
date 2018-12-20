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

import responses

from src.vinyldns.group import Group
from src.vinyldns.serdes import to_json_string, from_json_string
from tests import sampledata


def test_get_group(mocked_responses, vinyldns_client):
    g = {'name': 'ok'}
    mocked_responses.add(
        responses.GET, 'http://test.com/groups/123',
        body=json.dumps(g), status=200)
    r = vinyldns_client.get_group('123')
    assert r['name'] == 'ok'


def test_group_serdes():
    a = sampledata.sample_group
    print(to_json_string(a))
    b = from_json_string(to_json_string(a), Group.from_dict)
    assert a.id == b.id
    assert a.description == b.description
    assert a.created == b.created
    assert a.name == b.name
    assert all([l.__dict__ == r.__dict__ for l, r in zip(a.members, b.members)])
    assert all([l.__dict__ == r.__dict__ for l, r in zip(a.admins, b.admins)])

