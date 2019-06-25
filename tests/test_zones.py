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
from datetime import datetime

import responses

from sampledata import acl_rule, forward_zone, ip4_zone, ip6_zone, sample_zone_change
from vinyldns.serdes import to_json_string, from_json_string
from vinyldns.zone import Zone, ZoneChange, ListZonesResponse, ListZoneChangesResponse


def check_zone_connections_are_same(a, b):
    if a is None:
        assert b is None
    else:
        assert a.primary_server == b.primary_server
        assert a.key == b.key
        assert a.name == b.name
        assert a.key_name == b.key_name


def check_zones_are_same(a, b):
    assert a.id == b.id
    assert a.name == b.name
    assert a.email == b.email
    assert a.admin_group_id == b.admin_group_id
    assert a.status == b.status
    assert a.updated == b.updated
    assert a.created == b.created
    assert a.shared == b.shared
    assert a.backend_id == b.backend_id
    check_zone_connections_are_same(a.connection, b.connection)
    check_zone_connections_are_same(a.transfer_connection, b.transfer_connection)
    assert all([l.__dict__ == r.__dict__ for l, r in zip(a.acl.rules, b.acl.rules)])


def test_zone_serdes():
    s = to_json_string(forward_zone)
    print(json.dumps(s, indent=4))
    z = from_json_string(s, Zone.from_dict)

    assert z.name == forward_zone.name
    assert z.connection.primary_server == forward_zone.connection.primary_server
    assert all([a.__dict__ == b.__dict__ for a, b in zip(z.acl.rules, forward_zone.acl.rules)])


def test_connect_zone(mocked_responses, vinyldns_client):
    mocked_responses.add(
        responses.POST, 'http://test.com/zones',
        body=to_json_string(sample_zone_change), status=200)
    r = vinyldns_client.connect_zone(forward_zone)
    check_zones_are_same(forward_zone, r.zone)


def test_update_zone(mocked_responses, vinyldns_client):
    mocked_responses.add(
        responses.PUT, 'http://test.com/zones/{0}'.format(forward_zone.id),
        body=to_json_string(sample_zone_change), status=200)
    r = vinyldns_client.update_zone(forward_zone)
    check_zones_are_same(forward_zone, r.zone)


def test_abandon_zone(mocked_responses, vinyldns_client):
    mocked_responses.add(
        responses.DELETE, 'http://test.com/zones/{0}'.format(forward_zone.id),
        body=to_json_string(sample_zone_change), status=200)
    r = vinyldns_client.abandon_zone(forward_zone.id)
    check_zones_are_same(forward_zone, r.zone)


def test_sync_zone(mocked_responses, vinyldns_client):
    mocked_responses.add(
        responses.POST, 'http://test.com/zones/{0}/sync'.format(forward_zone.id),
        body=to_json_string(sample_zone_change), status=200)
    r = vinyldns_client.sync_zone(forward_zone.id)
    assert sample_zone_change.id == r.id
    assert sample_zone_change.change_type == r.change_type
    assert sample_zone_change.status == r.status
    assert sample_zone_change.system_message == r.system_message
    assert sample_zone_change.user_id == r.user_id
    check_zones_are_same(forward_zone, r.zone)


def test_list_zones(mocked_responses, vinyldns_client):
    lzr = ListZonesResponse(zones=[forward_zone, ip4_zone, ip6_zone], name_filter='*', start_from='start-from',
                            next_id='next', max_items=100)
    mocked_responses.add(
        responses.GET, 'http://test.com/zones?nameFilter=*&startFrom=start-from&maxItems=100',
        body=to_json_string(lzr), status=200
    )
    r = vinyldns_client.list_zones('*', 'start-from', 100)
    assert r.name_filter == lzr.name_filter
    assert r.start_from == lzr.start_from
    assert r.next_id == lzr.next_id
    assert r.max_items == lzr.max_items
    for l, r in zip(lzr.zones, r.zones):
        check_zones_are_same(l, r)


def test_get_zone(mocked_responses, vinyldns_client):
    mocked_responses.add(
        responses.GET, 'http://test.com/zones/{0}'.format(forward_zone.id),
        body=to_json_string({'zone': forward_zone}), status=200)
    r = vinyldns_client.get_zone(forward_zone.id)
    check_zones_are_same(forward_zone, r)


def test_get_zone_by_name(mocked_responses, vinyldns_client):
    mocked_responses.add(
        responses.GET, 'http://test.com/zones/name/{0}'.format(forward_zone.name),
        body=to_json_string({'zone': forward_zone}), status=200)
    r = vinyldns_client.get_zone_by_name(forward_zone.name)
    check_zones_are_same(forward_zone, r)


def test_list_zone_changes(mocked_responses, vinyldns_client):
    change1 = ZoneChange(zone=forward_zone, user_id='some-user', change_type='Create', status='Pending',
                         created=datetime.utcnow(), system_message=None, id='zone-change-id1')
    change2 = ZoneChange(zone=ip4_zone, user_id='some-user', change_type='Create', status='Pending',
                         created=datetime.utcnow(), system_message='msg', id='zone-change-id2')
    lzcr = ListZoneChangesResponse(forward_zone.id, [change1, change2], 'next', 'start', 100)
    mocked_responses.add(
        responses.GET, 'http://test.com/zones/{0}/changes?startFrom=start&maxItems=100'.format(forward_zone.id),
        body=to_json_string(lzcr), status=200
    )
    r = vinyldns_client.list_zone_changes(forward_zone.id, 'start', 100)
    assert r.start_from == lzcr.start_from
    assert r.next_id == lzcr.next_id
    assert r.max_items == lzcr.max_items
    for l, r in zip(lzcr.zone_changes, r.zone_changes):
        assert l.id == r.id
        assert l.user_id == r.user_id
        assert l.change_type == r.change_type
        assert l.status == r.status
        assert l.created == r.created
        assert l.system_message == r.system_message
        check_zones_are_same(l.zone, r.zone)


def test_add_acl_rule(mocked_responses, vinyldns_client):
    mocked_responses.add(
        responses.PUT, 'http://test.com/zones/{0}/acl/rules'.format(forward_zone.id),
        body=to_json_string(sample_zone_change)
    )
    r = vinyldns_client.add_zone_acl_rule(forward_zone.id, acl_rule)
    check_zones_are_same(r.zone, sample_zone_change.zone)


def test_delete_acl_rule(mocked_responses, vinyldns_client):
    mocked_responses.add(
        responses.DELETE, 'http://test.com/zones/{0}/acl/rules'.format(forward_zone.id),
        body=to_json_string(sample_zone_change)
    )
    r = vinyldns_client.delete_zone_acl_rule(forward_zone.id, acl_rule)
    check_zones_are_same(r.zone, sample_zone_change.zone)
