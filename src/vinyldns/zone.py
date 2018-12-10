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

        return Zone(d.get('id'), d.get('name'), d.get('email'), d.get('adminGroupId'), d.get('status'),
                    d.get('created'), d.get('updated'), conn, transfer_conn, acl,
                    d.get('latestSync'))
