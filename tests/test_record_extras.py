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

import copy
import json

import responses

from sampledata import forward_zone, record_set_values, gen_rs_change
from vinyldns.record import OwnershipTransferStatus
from vinyldns.serdes import to_json_string


def _request_json(request):
    body = request.body
    if isinstance(body, bytes):
        body = body.decode('utf-8')
    return json.loads(body)


def test_get_record_set_count(mocked_responses, vinyldns_client):
    mocked_responses.add(
        responses.GET, 'http://test.com/zones/{0}/recordsetcount'.format(forward_zone.id),
        body=to_json_string({'count': 5}), status=200)

    resp = vinyldns_client.get_record_set_count(forward_zone.id)
    assert resp.count == 5


def test_list_record_set_change_history(mocked_responses, vinyldns_client):
    change = gen_rs_change(list(record_set_values)[0])
    body = {
        'zoneId': forward_zone.id,
        'recordSetChanges': [change],
        'startFrom': 'start',
        'nextId': 'next',
        'maxItems': 100
    }
    mocked_responses.add(
        responses.GET,
        'http://test.com/recordsetchange/history?zoneId={0}&fqdn=rs.ok.&recordType=A&startFrom=start&maxItems=100'.format(
            forward_zone.id),
        body=to_json_string(body), status=200)

    resp = vinyldns_client.list_record_set_change_history(
        forward_zone.id, 'rs.ok.', 'A', start_from='start', max_items=100)
    assert resp.zone_id == forward_zone.id
    assert len(resp.record_set_changes) == 1


def test_list_record_set_changes_failure(mocked_responses, vinyldns_client):
    change = gen_rs_change(list(record_set_values)[0])
    body = {
        'failedRecordSetChanges': [change],
        'startFrom': 'start',
        'nextId': 'next',
        'maxItems': 100
    }
    mocked_responses.add(
        responses.GET,
        'http://test.com/metrics/health/zones/{0}/recordsetchangesfailure?startFrom=start&maxItems=100'.format(
            forward_zone.id),
        body=to_json_string(body), status=200)

    resp = vinyldns_client.list_record_set_changes_failure(forward_zone.id, start_from='start', max_items=100)
    assert len(resp.failed_record_set_changes) == 1


def test_record_set_ownership_request(mocked_responses, vinyldns_client):
    rs = copy.deepcopy(list(record_set_values)[0])
    rs.id = 'rs-id'

    def request_callback(request):
        payload = _request_json(request)
        group_change = payload.get('recordSetGroupChange')
        assert group_change['ownershipTransferStatus'] == OwnershipTransferStatus.Requested
        assert group_change['requestedOwnerGroupId'] == 'target-group'
        return (200, {}, to_json_string(gen_rs_change(rs)))

    mocked_responses.add_callback(
        responses.PUT,
        'http://test.com/zones/{0}/recordsets/{1}'.format(rs.zone_id, rs.id),
        callback=request_callback
    )

    vinyldns_client.request_record_set_ownership(rs, 'target-group')


def test_record_set_ownership_approve(mocked_responses, vinyldns_client):
    rs = copy.deepcopy(list(record_set_values)[0])
    rs.id = 'rs-id'

    def request_callback(request):
        payload = _request_json(request)
        group_change = payload.get('recordSetGroupChange')
        assert group_change['ownershipTransferStatus'] == OwnershipTransferStatus.ManuallyApproved
        assert group_change['requestedOwnerGroupId'] == 'target-group'
        assert payload.get('ownerGroupId') == 'target-group'
        return (200, {}, to_json_string(gen_rs_change(rs)))

    mocked_responses.add_callback(
        responses.PUT,
        'http://test.com/zones/{0}/recordsets/{1}'.format(rs.zone_id, rs.id),
        callback=request_callback
    )

    vinyldns_client.approve_record_set_ownership(rs, 'target-group')


def test_record_set_ownership_reject(mocked_responses, vinyldns_client):
    rs = copy.deepcopy(list(record_set_values)[0])
    rs.id = 'rs-id'

    def request_callback(request):
        payload = _request_json(request)
        group_change = payload.get('recordSetGroupChange')
        assert group_change['ownershipTransferStatus'] == OwnershipTransferStatus.ManuallyRejected
        assert group_change['requestedOwnerGroupId'] == 'target-group'
        return (200, {}, to_json_string(gen_rs_change(rs)))

    mocked_responses.add_callback(
        responses.PUT,
        'http://test.com/zones/{0}/recordsets/{1}'.format(rs.zone_id, rs.id),
        callback=request_callback
    )

    vinyldns_client.reject_record_set_ownership(rs, 'target-group')


def test_record_set_ownership_cancel(mocked_responses, vinyldns_client):
    rs = copy.deepcopy(list(record_set_values)[0])
    rs.id = 'rs-id'

    def request_callback(request):
        payload = _request_json(request)
        group_change = payload.get('recordSetGroupChange')
        assert group_change['ownershipTransferStatus'] == OwnershipTransferStatus.Cancelled
        assert group_change['requestedOwnerGroupId'] == 'target-group'
        return (200, {}, to_json_string(gen_rs_change(rs)))

    mocked_responses.add_callback(
        responses.PUT,
        'http://test.com/zones/{0}/recordsets/{1}'.format(rs.zone_id, rs.id),
        callback=request_callback
    )

    vinyldns_client.cancel_record_set_ownership(rs, 'target-group')
