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
from vinyldns.serdes import parse_datetime, map_option


class AccessLevel:
    NoAccess = "NoAccess"
    Read = "Read"
    Write = "Write"
    Delete = "Delete"


class ACLRule(object):
    def __init__(self, access_level, description=None, user_id=None, group_id=None, record_mask=None, record_types=[]):
        self.access_level = access_level
        self.description = description
        self.user_id = user_id
        self.group_id = group_id
        self.record_mask = record_mask
        self.record_types = record_types

    @staticmethod
    def from_dict(d):
        return ACLRule(access_level=d['accessLevel'], description=d.get('description'),
                       user_id=d.get('userId'), group_id=d.get('groupId'), record_mask=d.get('recordMask'),
                       record_types=d.get('recordTypes', []))


class ZoneACL(object):
    def __init__(self, rules=[]):
        self.rules = rules

    @staticmethod
    def from_dict(d):
        rules = [ACLRule.from_dict(r) for r in d.get('rules')] if d is not None else []
        return ZoneACL(rules)


class ZoneConnection(object):
    def __init__(self, name, key_name, key, primary_server):
        self.name = name
        self.key_name = key_name
        self.key = key
        self.primary_server = primary_server

    @staticmethod
    def from_dict(d):
        return ZoneConnection(name=d['name'], key_name=d['keyName'], key=d['key'],
                              primary_server=d['primaryServer']) if d is not None else None


class Zone(object):
    def __init__(self, id, name, email, admin_group_id, status=None, created=None, updated=None, connection=None,
                 transfer_connection=None, acl=ZoneACL(), latest_sync=None):
        self.id = id
        self.name = name
        self.email = email
        self.status = status
        self.created = created
        self.updated = updated
        self.connection = connection
        self.transfer_connection = transfer_connection
        self.acl = acl
        self.admin_group_id = admin_group_id
        self.latest_sync = latest_sync

    @staticmethod
    def from_dict(d):
        """
        from_dicts the string formatted json into a zone
        :param d: A dictionary built from json
        :return: A populated zone
        """
        conn = ZoneConnection.from_dict(d.get('connection'))
        transfer_conn = ZoneConnection.from_dict(d.get('transferConnection'))
        acl = ZoneACL.from_dict(d.get('acl'))
        created = map_option(d.get('created'), parse_datetime)
        updated = map_option(d.get('updated'), parse_datetime)
        latest_sync = map_option(d.get('latestSync'), parse_datetime)

        return Zone(d.get('id'), d.get('name'), d.get('email'), d.get('adminGroupId'), d.get('status'),
                    created,updated, conn, transfer_conn, acl, latest_sync)


class ListZonesResponse(object):
    def __init__(self, zones, name_filter, start_from, next_id, max_items):
        self.zones = zones
        self.name_filter = name_filter
        self.start_from = start_from
        self.next_id = next_id
        self.max_items = max_items

    @staticmethod
    def from_dict(d):
        zones = [Zone.from_dict(elem) for elem in d.get('zones', [])]
        return ListZonesResponse(zones=zones, name_filter=d.get('zoneFilter'), start_from=d.get('startFrom'),
                                 next_id=d.get('nextId'), max_items=d['maxItems'])


class ZoneChange(object):
    def __init__(self, zone, user_id, change_type, status, created, system_message, id):
        self.zone = zone
        self.user_id = user_id
        self.change_type = change_type
        self.status = status
        self.created = created
        self.system_message = system_message
        self.id = id

    @staticmethod
    def from_dict(d):
        zone = Zone.from_dict(d['zone'])
        created = map_option(d.get('created'), parse_datetime)
        return ZoneChange(zone=zone, user_id=d['userId'], change_type=d['changeType'], status=d['status'],
                          created=created, system_message=d.get('systemMessage'), id=d['id'])


class ListZoneChangesResponse(object):
    def __init__(self, zone_id, zone_changes, next_id, start_from, max_items):
        self.zone_id = zone_id
        self.zone_changes = zone_changes
        self.next_id = next_id
        self.start_from = start_from
        self.max_items = max_items

    @staticmethod
    def from_dict(d):
        zone_changes = [ZoneChange.from_dict(elem) for elem in d.get('zoneChanges', [])]
        return ListZoneChangesResponse(zone_id=d['zoneId'], zone_changes=zone_changes, next_id=d.get('nextId'),
                                       start_from=d.get('startFrom'), max_items=d['maxItems'])
