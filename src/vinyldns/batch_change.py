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

from vinyldns.serdes import parse_datetime, map_option, to_utc_strftime
from vinyldns.record import rdata_converters
import json


def to_review_json(s):
    """
    Converts the string to json
    :param s: A string
    :return: A json formatted string representation of the object
    """
    b = {}
    if s:
        b.update({"reviewComment": s})
        return json.dumps(b)
    else:
        return None


class AddRecord(object):
    def __init__(self, input_name, type, ttl, record):
        self.input_name = input_name
        self.type = type
        self.ttl = ttl
        self.record = record
        self.change_type = 'Add'

    @staticmethod
    def from_dict(d):
        return AddRecord(
            input_name=d['inputName'],
            type=d['type'],
            ttl=d['ttl'],
            record=d['record']
        )


class DeleteRecordSet(object):
    def __init__(self, input_name, type):
        self.input_name = input_name
        self.type = type
        self.change_type = 'DeleteRecordSet'

    @staticmethod
    def from_dict(d):
        return DeleteRecordSet(
            input_name=d['inputName'],
            type=d['type']
        )


class ValidationError(object):
    def __init__(self, error_type, message):
        self.error_type = error_type
        self.message = message

    @staticmethod
    def from_dict(d):
        return ValidationError(
            error_type=d['errorType'],
            message=d['message']
        )


class BatchChangeRequest(object):
    change_type_converters = {
        'Add': AddRecord.from_dict,
        'DeleteRecordSet': DeleteRecordSet.from_dict
    }

    def __init__(self, changes, comments=None, owner_group_id=None,
                 scheduled_time=None):
        self.comments = comments
        self.changes = changes
        self.owner_group_id = owner_group_id
        self.scheduled_time = to_utc_strftime(scheduled_time) if scheduled_time else None

    @staticmethod
    def from_dict(d):
        return BatchChangeRequest(
            comments=d.get('comments'),
            changes=[BatchChangeRequest.change_type_converters[elem['changeType']](elem)
                     for elem in d.get('changes', [])],
            owner_group_id=d.get('ownerGroupId'),
            scheduled_time=map_option(d.get('scheduledTime'), parse_datetime)
        )


class AddRecordChange(object):
    def __init__(self, zone_id, zone_name, record_name, input_name, type, ttl,
                 record, status, id, validation_errors, system_message=None,
                 record_change_id=None, record_set_id=None):
        self.zone_id = zone_id
        self.zone_name = zone_name
        self.record_name = record_name
        self.input_name = input_name
        self.type = type
        self.ttl = ttl
        self.record = record
        self.status = status
        self.id = id
        self.system_message = system_message
        self.record_change_id = record_change_id
        self.record_set_id = record_set_id
        self.change_type = 'Add'
        self.validation_errors = validation_errors

    @staticmethod
    def from_dict(d):
        return AddRecordChange(
            zone_id=d['zoneId'],
            zone_name=d['zoneName'],
            record_name=d['recordName'],
            input_name=d['inputName'],
            type=d['type'],
            ttl=d['ttl'],
            record=rdata_converters[d['type']](d['record']),
            status=d['status'],
            id=d['id'],
            system_message=d.get('systemMessage'),
            record_change_id=d.get('recordChangeId'),
            record_set_id=d.get('recordSetId'),
            validation_errors=[ValidationError.from_dict(elem) for elem in d.get('validationErrors', [])]
        )


class DeleteRecordSetChange(object):
    def __init__(self, zone_id, zone_name, record_name, input_name, type, status,
                 id, validation_errors, system_message=None, record_change_id=None, record_set_id=None):
        self.zone_id = zone_id
        self.zone_name = zone_name
        self.record_name = record_name
        self.input_name = input_name
        self.type = type
        self.status = status
        self.id = id
        self.system_message = system_message
        self.record_change_id = record_change_id
        self.record_set_id = record_set_id
        self.change_type = 'DeleteRecordSet'
        self.validation_errors = validation_errors

    @staticmethod
    def from_dict(d):
        return DeleteRecordSetChange(
            zone_id=d['zoneId'],
            zone_name=d['zoneName'],
            record_name=d['recordName'],
            input_name=d['inputName'],
            type=d['type'],
            status=d['status'],
            id=d['id'],
            system_message=d.get('systemMessage'),
            record_change_id=d.get('recordChangeId'),
            record_set_id=d.get('recordSetId'),
            validation_errors=[ValidationError.from_dict(elem) for elem in d.get('validation_errors', [])]
        )


class BatchChange(object):
    change_type_converters = {
        'Add': AddRecordChange.from_dict,
        'DeleteRecordSet': DeleteRecordSetChange.from_dict
    }

    def __init__(self, user_id, user_name, created_timestamp, changes, id,
                 status, approval_status, comments=None, owner_group_id=None,
                 owner_group_name=None, reviewer_id=None,
                 reviewer_user_name=None, review_comment=None,
                 review_timestamp=None, scheduled_time=None):
        self.user_id = user_id
        self.user_name = user_name
        self.comments = comments
        self.created_timestamp = created_timestamp
        self.changes = changes
        self.id = id
        self.status = status
        self.owner_group_id = owner_group_id
        self.owner_group_name = owner_group_name
        self.approval_status = approval_status
        self.reviewer_id = reviewer_id
        self.reviewer_user_name = reviewer_user_name
        self.review_comment = review_comment
        self.review_timestamp = review_timestamp
        self.scheduled_time = scheduled_time

    @staticmethod
    def from_dict(d):
        return BatchChange(
            user_id=d['userId'],
            user_name=d['userName'],
            comments=d.get('comments'),
            created_timestamp=map_option(d.get('createdTimestamp'), parse_datetime),
            changes=[BatchChange.change_type_converters[elem['changeType']](elem) for elem in d.get('changes', [])],
            id=d['id'],
            status=d['status'],
            owner_group_id=d.get('ownerGroupId'),
            owner_group_name=d.get('ownerGroupName'),
            approval_status=d['approvalStatus'],
            reviewer_id=d.get('reviewerId'),
            reviewer_user_name=d.get('reviewerUserName'),
            review_comment=d.get('reviewComment'),
            review_timestamp=map_option(d.get('reviewTimestamp'), parse_datetime),
            scheduled_time=map_option(d.get('scheduledTime'), parse_datetime)
        )


class BatchChangeSummary(object):
    def __init__(self, user_id, user_name, created_timestamp, total_changes, id,
                 status, approval_status, comments=None, owner_group_id=None,
                 owner_group_name=None, reviewer_id=None,
                 reviewer_user_name=None, review_comment=None,
                 review_timestamp=None, scheduled_time=None):
        self.user_id = user_id
        self.user_name = user_name
        self.comments = comments
        self.created_timestamp = created_timestamp
        self.total_changes = total_changes
        self.status = status
        self.id = id
        self.owner_group_id = owner_group_id
        self.owner_group_name = owner_group_name
        self.approval_status = approval_status
        self.reviewer_id = reviewer_id
        self.reviewer_user_name = reviewer_user_name
        self.review_comment = review_comment
        self.review_timestamp = review_timestamp
        self.scheduled_time = scheduled_time

    @staticmethod
    def from_dict(d):
        return BatchChangeSummary(
            user_id=d['userId'],
            user_name=d['userName'],
            comments=d.get('comments'),
            created_timestamp=parse_datetime(d['createdTimestamp']),
            total_changes=d['totalChanges'],
            status=d['status'],
            id=d['id'],
            owner_group_id=d.get('ownerGroupId'),
            owner_group_name=d.get('ownerGroupName'),
            approval_status=d['approvalStatus'],
            reviewer_id=d.get('reviewerId'),
            reviewer_user_name=d.get('reviewerUserName'),
            review_comment=d.get('reviewComment'),
            review_timestamp=d.get('reviewTimestamp'),
            scheduled_time=map_option(d.get('scheduledTime'), parse_datetime)
        )


class ListBatchChangeSummaries(object):
    def __init__(self, batch_changes, start_from=None, next_id=None,
                 max_items=100, ignore_access=False, approval_status=None):
        self.batch_changes = batch_changes
        self.start_from = start_from
        self.next_id = next_id
        self.max_items = max_items
        self.ignore_access = ignore_access
        self.approval_status = approval_status

    @staticmethod
    def from_dict(d):
        return ListBatchChangeSummaries(
            batch_changes=[BatchChangeSummary.from_dict(elem) for elem in d.get('batchChanges', [])],
            start_from=d.get('startFrom'),
            next_id=d.get('nextId'),
            max_items=d.get('maxItems', 100),
            ignore_access=d.get('ignoreAccess'),
            approval_status=d.get('approvalStatus')
        )
