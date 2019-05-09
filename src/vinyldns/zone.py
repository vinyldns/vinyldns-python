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
        rules = [ACLRule.from_dict(r) for r in d.get('rules', [])]
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
                              primary_server=d['primaryServer'])


class Zone(object):
    def __init__(self, name, email, admin_group_id, id=None, status=None, created=None, updated=None, connection=None,
                 transfer_connection=None, acl=ZoneACL(), latest_sync=None, is_test=False, shared=False,
                 backend_id=None):
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
        self.is_test = is_test
        self.shared = shared
        self.backend_id = backend_id

    @staticmethod
    def from_dict(d):
        """
        from_dicts the string formatted json into a zone
        :param d: A dictionary built from json
        :return: A populated zone
        """
        return Zone(
            id=d['id'],
            name=d['name'],
            email=d['email'],
            admin_group_id=d['adminGroupId'],
            status=d.get('status'),
            created=map_option(d.get('created'), parse_datetime),
            updated=map_option(d.get('updated'), parse_datetime),
            connection=map_option(d.get('connection'), ZoneConnection.from_dict),
            transfer_connection=map_option(d.get('transferConnection'), ZoneConnection.from_dict),
            acl=map_option(d.get('acl'), ZoneACL.from_dict),
            latest_sync=map_option(d.get('latestSync'), parse_datetime),
            is_test=d.get('isTest', False),
            shared=d['shared'],
            backend_id=d.get('backendId')
        )


class ListZonesResponse(object):
    def __init__(self, zones, name_filter, start_from=None, next_id=None, max_items=100):
        self.zones = zones
        self.name_filter = name_filter
        self.start_from = start_from
        self.next_id = next_id
        self.max_items = max_items

    @staticmethod
    def from_dict(d):
        zones = [Zone.from_dict(elem) for elem in d.get('zones', [])]
        return ListZonesResponse(zones=zones, name_filter=d.get('nameFilter'), start_from=d.get('startFrom'),
                                 next_id=d.get('nextId'), max_items=d.get('maxItems', 100))


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
    def __init__(self, zone_id, zone_changes, start_from=None, next_id=None, max_items=100):
        self.zone_id = zone_id
        self.zone_changes = zone_changes
        self.next_id = next_id
        self.start_from = start_from
        self.max_items = max_items

    @staticmethod
    def from_dict(d):
        zone_changes = [ZoneChange.from_dict(elem) for elem in d.get('zoneChanges', [])]
        return ListZoneChangesResponse(zone_id=d['zoneId'], zone_changes=zone_changes, next_id=d.get('nextId'),
                                       start_from=d.get('startFrom'), max_items=d.get('maxItems', 100))
