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


class UserLockStatus:
    Unlocked = "Unlocked"
    Locked = "Locked"


class User(object):
    def __init__(self, id, user_name=None, first_name=None, last_name=None, email=None, created=None,
                 lock_status=UserLockStatus.Unlocked):
        self.id = id
        self.user_name = user_name
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.created = created
        self.lock_status = lock_status

    @staticmethod
    def from_dict(d):
        return User(id=d['id'], user_name=d.get('userName'), first_name=d.get('firstName'), last_name=d.get('lastName'),
                    email=d.get('email'), lock_status=d.get('lockStatus', UserLockStatus.Unlocked))


class Group(object):
    def __init__(self, name, email, description=None, created=None, members=[], admins=[], id=None):
        self.name = name
        self.email = email
        self.description = description
        self.created = created
        self.members = members
        self.admins = admins
        self.id = id

    @staticmethod
    def from_dict(d):
        members = [User.from_dict(ud) for ud in d.get('members', [])]
        admins =[User.from_dict(ud) for ud in d.get('admins', [])]
        return Group(name=d['name'], email=d['email'], description=d.get('description'), created=d.get('created'),
                     members=members, admins=admins, id=d.get('id'))


class ListGroupsResponse(object):
    def __init__(self, groups, max_items, group_name_filter=None, start_from=None, next_id=None):
        self.groups = groups
        self.max_items = max_items
        self.group_name_filter = group_name_filter
        self.start_from = start_from
        self.next_id = next_id

    @staticmethod
    def from_dict(d):
        groups = [Group.from_dict(elem) for elem in d.get('groups', [])]
        return ListGroupsResponse(groups, d['maxItems'], d.get('groupNameFilter'), d.get('startFrom'), d.get('nextId'))


class GroupChange(object):
    def __init__(self, new_group, change_type, user_id, old_group, id, created):
        self.new_group = new_group
        self.change_type = change_type
        self.user_id = user_id
        self.old_group = old_group
        self.id = id
        self.created = created

    @staticmethod
    def from_dict(d):
        return
