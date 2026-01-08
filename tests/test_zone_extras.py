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

from sampledata import sample_zone_change, forward_zone
from vinyldns.serdes import to_json_string


def test_get_zone_details(mocked_responses, vinyldns_client):
    body = {
        'zone': {
            'name': forward_zone.name,
            'email': forward_zone.email,
            'status': 'Active',
            'adminGroupId': forward_zone.admin_group_id,
            'adminGroupName': 'admins'
        }
    }
    mocked_responses.add(
        responses.GET, 'http://test.com/zones/{0}/details'.format(forward_zone.id),
        body=to_json_string(body), status=200)

    details = vinyldns_client.get_zone_details(forward_zone.id)
    assert details.admin_group_name == 'admins'
    assert details.admin_group_id == forward_zone.admin_group_id


def test_list_zone_backend_ids(mocked_responses, vinyldns_client):
    mocked_responses.add(
        responses.GET, 'http://test.com/zones/backendids',
        body=to_json_string({'backendIds': ['b1', 'b2']}), status=200)

    assert vinyldns_client.list_zone_backend_ids() == ['b1', 'b2']


def test_list_zone_changes_failure(mocked_responses, vinyldns_client):
    body = {
        'failedZoneChanges': [sample_zone_change],
        'startFrom': 'start',
        'nextId': 'next',
        'maxItems': 100
    }
    mocked_responses.add(
        responses.GET, 'http://test.com/metrics/health/zonechangesfailure?startFrom=start&maxItems=100',
        body=to_json_string(body), status=200)

    resp = vinyldns_client.list_zone_changes_failure(start_from='start', max_items=100)
    assert resp.start_from == 'start'
    assert resp.next_id == 'next'
    assert len(resp.failed_zone_changes) == 1


def test_list_deleted_zones(mocked_responses, vinyldns_client):
    body = {
        'zonesDeletedInfo': [{
            'zoneChange': sample_zone_change,
            'adminGroupName': 'admins',
            'userName': 'user',
            'accessLevel': 'Read'
        }],
        'startFrom': 'start',
        'nextId': 'next',
        'maxItems': 100,
        'ignoreAccess': True
    }
    mocked_responses.add(
        responses.GET, 'http://test.com/zones/deleted/changes?startFrom=start&maxItems=100&ignoreAccess=True',
        body=to_json_string(body), status=200)

    resp = vinyldns_client.list_deleted_zones(start_from='start', max_items=100, ignore_access=True)
    assert resp.ignore_access is True
    assert len(resp.zones_deleted_info) == 1
