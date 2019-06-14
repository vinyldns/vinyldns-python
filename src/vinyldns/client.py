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
import logging
import os
from builtins import str

import requests
from future.moves.urllib.parse import parse_qs
from future.utils import iteritems
from requests.adapters import HTTPAdapter
# Python 2/3 compatibility
from requests.compat import urljoin
from requests.compat import urlparse
from requests.compat import urlsplit
from requests.packages.urllib3.util.retry import Retry

# TODO: Didn't like this boto request signer, fix when moving back
from vinyldns.boto_request_signer import BotoRequestSigner

from vinyldns.batch_change import BatchChange, ListBatchChangeSummaries
from vinyldns.membership import Group, ListGroupsResponse, ListGroupChangesResponse, ListMembersResponse, \
    ListAdminsResponse
from vinyldns.serdes import to_json_string
from vinyldns.zone import ListZonesResponse, ListZoneChangesResponse, Zone, ZoneChange
from vinyldns.record import ListRecordSetsResponse, ListRecordSetChangesResponse, RecordSet, RecordSetChange

try:
    basestring
except NameError:
    basestring = str

logger = logging.getLogger(__name__)

__all__ = [u'VinylDNSClient', u'MAX_RETRIES', u'RETRY_WAIT']

MAX_RETRIES = 30
RETRY_WAIT = 0.05


class ClientError(Exception):
    """Base class for custom exceptions"""
    pass


class BadRequestError(ClientError):
    """400 Bad Request error"""
    pass


class UnauthorizedError(ClientError):
    """401 Unauthorized error"""
    pass


class ForbiddenError(ClientError):
    """403 Forbidden Error"""
    pass


class ConflictError(ClientError):
    """409 Conflict error"""
    pass


class UnprocessableError(ClientError):
    """422 Unprocessable Entity error"""
    pass


class VinylDNSClient(object):
    """TODO: Add class docstring."""

    def __init__(self, url, access_key, secret_key):
        """TODO: Add method docstring."""
        self.index_url = url
        self.headers = {
            u'Accept': u'application/json, text/plain',
            u'Content-Type': u'application/json'
        }

        self.signer = BotoRequestSigner(self.index_url,
                                        access_key, secret_key)

        self.session = self.__requests_retry_session()

    @classmethod
    def from_env(cls):
        """
        Create client from environment variables.

        :return: a client instance
        """
        url = os.environ.get('VINYLDNS_API_URL')
        access_key = os.environ.get('VINYLDNS_ACCESS_KEY_ID')
        secret_key = os.environ.get('VINYLDNS_SECRET_ACCESS_KEY')

        if url is None or access_key is None or secret_key is None:
            raise Exception('\'VINYLDNS_API_URL\', \'VINYLDNS_ACCESS_KEY_ID\', '
                            '\'VINYLDNS_SECRET_ACCESS_KEY\' environment variables'
                            'are required.')
        return cls(url, access_key, secret_key)

    def __requests_retry_session(self,
                                 retries=5,
                                 backoff_factor=0.4,
                                 status_forcelist=(500, 502, 504),
                                 session=None):

        session = session or requests.Session()
        retry = Retry(
            total=retries,
            read=retries,
            connect=retries,
            backoff_factor=backoff_factor,
            status_forcelist=status_forcelist,
        )
        adapter = HTTPAdapter(max_retries=retry)
        session.mount(u'http://', adapter)
        session.mount(u'https://', adapter)
        return session

    def __make_request(self, url, method=u'GET', headers=None, body_string=None, **kwargs):

        # remove retries arg if provided
        kwargs.pop(u'retries', None)

        path = urlparse(url).path

        # we must parse the query string so we can provide it if it exists so that we can pass it to the
        # build_vinyldns_request so that it can be properly included in the AWS signing...
        query = parse_qs(urlsplit(url).query)

        if query:
            # the problem with parse_qs is that it will return a list for ALL params, even if they are a single value
            # we need to essentially flatten the params if a param has only one value
            query = dict((k, v if len(v) > 1 else v[0])
                         for k, v in iteritems(query))

        signed_headers, signed_body = self.__build_vinyldns_request(method, path, body_string, query,
                                                                    with_headers=headers or {}, **kwargs)
        response = self.session.request(method, url, data=signed_body, headers=signed_headers, **kwargs)

        return self.__check_response(response)

    def __check_response(self, response):
        status = response.status_code
        if status == 200 or status == 202:
            return response.status_code, response.json()
        elif status == 400:
            raise BadRequestError(response.text)
        elif status == 401:
            raise UnauthorizedError(response.text)
        elif status == 403:
            raise ForbiddenError(response.text)
        elif status == 404:
            return 404, None
        elif status == 409:
            raise ConflictError(response.text)
        elif status == 422:
            raise UnprocessableError(response.text)
        else:
            raise ClientError(response.text)

    def __build_vinyldns_request(self, method, path, body_data, params=None, **kwargs):

        if isinstance(body_data, basestring):
            body_string = body_data
        else:
            body_string = json.dumps(body_data)

        new_headers = {u'X-Amz-Target': u'VinylDNS'}
        new_headers.update(kwargs.get(u'with_headers', dict()))

        suppress_headers = kwargs.get(u'suppress_headers', list())

        headers = self.__build_headers(new_headers, suppress_headers)

        auth_header = self.signer.build_auth_header(method, path, headers, body_string, params)
        headers[u'Authorization'] = auth_header

        return headers, body_string

    @staticmethod
    def __build_headers(new_headers, suppressed_keys):

        def canonical_header_name(field_name):
            return u'-'.join(word.capitalize() for word in field_name.split(u'-'))

        import datetime
        now = datetime.datetime.utcnow()
        headers = {u'Content-Type': u'application/x-amz-json-1.0',
                   u'Date': now.strftime(u'%a, %d %b %Y %H:%M:%S GMT'),
                   u'X-Amz-Date': now.strftime(u'%Y%m%dT%H%M%SZ')}

        for k, v in iteritems(new_headers):
            headers[canonical_header_name(k)] = v

        for k in map(canonical_header_name, suppressed_keys):
            if k in headers:
                del headers[k]

        return headers

    def create_group(self, group, **kwargs):
        """
        Create a new group.

        :param group: A group dictionary that can be serialized to json
        :return: the content of the response, which should be a group json
        """
        url = urljoin(self.index_url, u'/groups')
        response, data = self.__make_request(url, u'POST', self.headers, to_json_string(group), **kwargs)

        return Group.from_dict(data)

    def get_group(self, group_id, **kwargs):
        """
        Get a group.

        :param group_id: Id of the group to get
        :return: the group json
        """
        url = urljoin(self.index_url, u'/groups/' + group_id)
        response, data = self.__make_request(url, u'GET', self.headers, **kwargs)

        return Group.from_dict(data) if data is not None else None

    def delete_group(self, group_id, **kwargs):
        """
        Delete a group.

        :param group_id: Id of the group to delete
        :return: the group json
        """
        url = urljoin(self.index_url, u'/groups/' + group_id)
        response, data = self.__make_request(url, u'DELETE', self.headers, **kwargs)

        return Group.from_dict(data)

    def update_group(self, group, **kwargs):
        """
        Update an existing group, uses the id of the group provided

        :param group: A group to be updated
        :return: the content of the response, which should be a group json
        """
        url = urljoin(self.index_url, u'/groups/{0}'.format(group.id))
        response, data = self.__make_request(url, u'PUT', self.headers, to_json_string(group), **kwargs)

        return Group.from_dict(data)

    def list_my_groups(self, group_name_filter=None, start_from=None, max_items=None, **kwargs):
        """
        Retrieve my groups.

        :param start_from: the start key of the page; this is the next_id of a prior call
        :param max_items: the number of groups to return
        :param group_name_filter: only returns groups whose names contain filter string
        :return: the content of the response
        """
        args = []
        if group_name_filter:
            args.append(u'groupNameFilter={0}'.format(group_name_filter))
        if start_from:
            args.append(u'startFrom={0}'.format(start_from))
        if max_items is not None:
            args.append(u'maxItems={0}'.format(max_items))

        url = urljoin(self.index_url, u'/groups') + u'?' + u'&'.join(args)
        response, data = self.__make_request(url, u'GET', self.headers, **kwargs)

        return ListGroupsResponse.from_dict(data)

    def list_all_my_groups(self, group_name_filter=None, **kwargs):
        """
        Retrieve all my groups, paging through the results until exhausted

        :param group_name_filter: only returns groups whose names contain filter string
        :return: the content of the response
        """
        groups = []
        args = []
        if group_name_filter:
            args.append(u'groupNameFilter={0}'.format(group_name_filter))

        url = urljoin(self.index_url, u'/groups') + u'?' + u'&'.join(args)
        response, data = self.__make_request(url, u'GET', self.headers, **kwargs)
        groups.extend(data[u'groups'])

        while u'nextId' in data and data[u'nextId']:
            next_args = args[:]
            next_args.append(u'startFrom={0}'.format(data['nextId']))
            url = urljoin(self.index_url, u'/groups') + u'?' + u'&'.join(next_args)
            response, data = self.__make_request(url, u'GET', self.headers, **kwargs)
            groups.extend(data[u'groups'])

        g = [Group.from_dict(elem) for elem in groups]
        return ListGroupsResponse(groups=g, group_name_filter=group_name_filter)

    def list_members_group(self, group_id, start_from=None, max_items=None, **kwargs):
        """
        List the members of an existing group.

        :param group_id: the Id of an existing group
        :param start_from: the Id a member of the group
        :param max_items: the max number of items to be returned
        :return: the json of the members
        """
        if start_from is None and max_items is None:
            url = urljoin(self.index_url, u'/groups/{0}/members'.format(group_id))
        elif start_from is None and max_items is not None:
            url = urljoin(self.index_url, u'/groups/{0}/members?maxItems={1}'.format(group_id, max_items))
        elif start_from is not None and max_items is None:
            url = urljoin(self.index_url, u'/groups/{0}/members?startFrom={1}'.format(group_id, start_from))
        elif start_from is not None and max_items is not None:
            url = urljoin(self.index_url, u'/groups/{0}/members?startFrom={1}&maxItems={2}'.format(group_id,
                                                                                                   start_from,
                                                                                                   max_items))

        response, data = self.__make_request(url, u'GET', self.headers, **kwargs)

        return ListMembersResponse.from_dict(data)

    def list_group_admins(self, group_id, **kwargs):
        """
        Return the group admins.

        :param group_id: the Id of the group
        :return: the user info of the admins
        """
        url = urljoin(self.index_url, u'/groups/{0}/admins'.format(group_id))
        response, data = self.__make_request(url, u'GET', self.headers, **kwargs)

        return ListAdminsResponse.from_dict(data)

    def list_group_changes(self, group_id, start_from=None, max_items=None, **kwargs):
        """
        List the changes of an existing group.

        :param group_id: the Id of an existing group
        :param start_from: the Id a group change
        :param max_items: the max number of items to be returned
        :return: the json of the members
        """
        if start_from is None and max_items is None:
            url = urljoin(self.index_url, u'/groups/{0}/activity'.format(group_id))
        elif start_from is None and max_items is not None:
            url = urljoin(self.index_url, u'/groups/{0}/activity?maxItems={1}'.format(group_id, max_items))
        elif start_from is not None and max_items is None:
            url = urljoin(self.index_url, u'/groups/{0}/activity?startFrom={1}'.format(group_id, start_from))
        elif start_from is not None and max_items is not None:
            url = urljoin(self.index_url, u'/groups/{0}/activity?startFrom={1}&maxItems={2}'.format(group_id,
                                                                                                    start_from,
                                                                                                    max_items))

        response, data = self.__make_request(url, u'GET', self.headers, **kwargs)

        return ListGroupChangesResponse.from_dict(data)

    def connect_zone(self, zone, **kwargs):
        """
        Create a new zone with the given name and email.

        :param zone: the zone to be created
        :return: the content of the response
        """
        url = urljoin(self.index_url, u'/zones')
        response, data = self.__make_request(url, u'POST', self.headers, to_json_string(zone), **kwargs)
        return ZoneChange.from_dict(data)

    def update_zone(self, zone, **kwargs):
        """
        Update a zone.

        :param zone: the zone to be created
        :return: the content of the response
        """
        url = urljoin(self.index_url, u'/zones/{0}'.format(zone.id))
        response, data = self.__make_request(url, u'PUT', self.headers, to_json_string(zone), **kwargs)
        return ZoneChange.from_dict(data)

    def sync_zone(self, zone_id, **kwargs):
        """
        Sync a zone.

        :param zone: the zone to be updated
        :return: the content of the response
        """
        url = urljoin(self.index_url, u'/zones/{0}/sync'.format(zone_id))
        response, data = self.__make_request(url, u'POST', self.headers, **kwargs)

        return ZoneChange.from_dict(data)

    def abandon_zone(self, zone_id, **kwargs):
        """
        Delete the zone for the given id.

        :param zone_id: the id of the zone to be deleted
        :return: nothing, will fail if the status code was not expected
        """
        url = urljoin(self.index_url, u'/zones/{0}'.format(zone_id))
        response, data = self.__make_request(url, u'DELETE', self.headers, **kwargs)

        return ZoneChange.from_dict(data)

    def get_zone(self, zone_id, **kwargs):
        """
        Get a zone for the given zone id.

        :param zone_id: the id of the zone to retrieve
        :return: the zone, or will 404 if not found
        """
        url = urljoin(self.index_url, u'/zones/{0}'.format(zone_id))
        response, data = self.__make_request(url, u'GET', self.headers, **kwargs)

        return Zone.from_dict(data['zone']) if data is not None else None

    def list_zone_changes(self, zone_id, start_from=None, max_items=None, **kwargs):
        """
        Get the zone changes for the given zone id.

        :param zone_id: the id of the zone to retrieve
        :param start_from: the start key of the page
        :param max_items: the page limit
        :return: the zone, or will 404 if not found
        """
        args = []
        if start_from:
            args.append(u'startFrom={0}'.format(start_from))
        if max_items is not None:
            args.append(u'maxItems={0}'.format(max_items))
        url = urljoin(self.index_url, u'/zones/{0}/changes'.format(zone_id)) + u'?' + u'&'.join(args)

        response, data = self.__make_request(url, u'GET', self.headers, **kwargs)
        return ListZoneChangesResponse.from_dict(data)

    def list_zones(self, name_filter=None, start_from=None, max_items=None, **kwargs):
        """
        Get a list of zones that currently exist.

        :return: a list of zones
        """
        url = urljoin(self.index_url, u'/zones')

        query = []
        if name_filter:
            query.append(u'nameFilter=' + name_filter)

        if start_from:
            query.append(u'startFrom=' + str(start_from))

        if max_items:
            query.append(u'maxItems=' + str(max_items))

        if query:
            url = url + u'?' + u'&'.join(query)

        response, data = self.__make_request(url, u'GET', self.headers, **kwargs)
        return ListZonesResponse.from_dict(data)

    def create_record_set(self, record_set, **kwargs):
        """
        Create a new record_set.

        :param record_set: the record_set to be created
        :return: the content of the response
        """
        url = urljoin(self.index_url, u'/zones/{0}/recordsets'.format(record_set.zone_id))
        response, data = self.__make_request(url, u'POST', self.headers, to_json_string(record_set), **kwargs)
        return RecordSetChange.from_dict(data)

    def delete_record_set(self, zone_id, rs_id, **kwargs):
        """
        Delete an existing record_set.

        :param zone_id: the zone id the record_set belongs to
        :param rs_id: the id of the record_set to be deleted
        :return: the content of the response
        """
        url = urljoin(self.index_url, u'/zones/{0}/recordsets/{1}'.format(zone_id, rs_id))

        response, data = self.__make_request(url, u'DELETE', self.headers, **kwargs)
        return RecordSetChange.from_dict(data)

    def update_record_set(self, record_set, **kwargs):
        """
        Delete an existing record_set.

        :param record_set: the record_set to be updated
        :return: the content of the response
        """
        url = urljoin(self.index_url, u'/zones/{0}/recordsets/{1}'.format(record_set.zone_id, record_set.id))

        response, data = self.__make_request(url, u'PUT', self.headers,
                                             to_json_string(record_set), **kwargs)

        return RecordSetChange.from_dict(data)

    def get_record_set(self, zone_id, rs_id, **kwargs):
        """
        Get an existing record_set.

        :param zone_id: the zone id the record_set belongs to
        :param rs_id: the id of the record_set to be retrieved
        :return: the content of the response
        """
        url = urljoin(self.index_url, u'/zones/{0}/recordsets/{1}'.format(zone_id, rs_id))

        response, data = self.__make_request(url, u'GET', self.headers, None, **kwargs)
        return RecordSet.from_dict(data['recordSet']) if data is not None else None

    def list_record_sets(self, zone_id, start_from=None, max_items=None, record_name_filter=None, **kwargs):
        """
        Retrieve record_sets in a zone.

        :param zone_id: the zone to retrieve
        :param start_from: the start key of the page
        :param max_items: the page limit
        :param record_name_filter: only returns record_sets whose names contain filter string
        :return: the content of the response
        """
        args = []
        if start_from:
            args.append(u'startFrom={0}'.format(start_from))
        if max_items is not None:
            args.append(u'maxItems={0}'.format(max_items))
        if record_name_filter:
            args.append(u'recordNameFilter={0}'.format(record_name_filter))

        url = urljoin(self.index_url, u'/zones/{0}/recordsets'.format(zone_id)) + u'?' + u'&'.join(args)

        response, data = self.__make_request(url, u'GET', self.headers, **kwargs)
        return ListRecordSetsResponse.from_dict(data)

    def get_record_set_change(self, zone_id, rs_id, change_id, **kwargs):
        """
        Get an existing record_set change.

        :param zone_id: the zone id the record_set belongs to
        :param rs_id: the id of the record_set to be retrieved
        :param change_id: the id of the change to be retrieved
        :return: the content of the response
        """
        url = urljoin(self.index_url, u'/zones/{0}/recordsets/{1}/changes/{2}'.format(zone_id, rs_id, change_id))

        response, data = self.__make_request(url, u'GET', self.headers, None, **kwargs)
        return RecordSetChange.from_dict(data) if data is not None else None

    def list_record_set_changes(self, zone_id, start_from=None, max_items=None, **kwargs):
        """
        Get the record_set changes for the given zone id.

        :param zone_id: the id of the zone to retrieve
        :param start_from: the start key of the page
        :param max_items: the page limit
        :return: the zone, or will 404 if not found
        """
        args = []
        if start_from:
            args.append(u'startFrom={0}'.format(start_from))
        if max_items is not None:
            args.append(u'maxItems={0}'.format(max_items))
        url = urljoin(self.index_url, u'/zones/{0}/recordsetchanges'.format(zone_id)) + u'?' + u'&'.join(args)

        response, data = self.__make_request(url, u'GET', self.headers, **kwargs)
        return ListRecordSetChangesResponse.from_dict(data)

    def create_batch_change(self, batch_change_input, **kwargs):
        """
        Create a new batch change.

        :param batch_change_input: the batchchange to be created
        :return: the content of the response
        """
        url = urljoin(self.index_url, u'/zones/batchrecordchanges')
        response, data = self.__make_request(url, u'POST', self.headers, to_json_string(batch_change_input), **kwargs)
        return BatchChange.from_dict(data)

    def get_batch_change(self, batch_change_id, **kwargs):
        """
        Get an existing batch change.

        :param batch_change_id: the unique identifier of the batchchange
        :return: the content of the response
        """
        url = urljoin(self.index_url, u'/zones/batchrecordchanges/{0}'.format(batch_change_id))
        response, data = self.__make_request(url, u'GET', self.headers, None, **kwargs)
        return BatchChange.from_dict(data) if data is not None else None

    def list_batch_change_summaries(self, start_from=None, max_items=None, **kwargs):
        """
        Get list of user's batch change summaries.

        :return: the content of the response
        """
        args = []
        if start_from:
            args.append(u'startFrom={0}'.format(start_from))
        if max_items is not None:
            args.append(u'maxItems={0}'.format(max_items))

        url = urljoin(self.index_url, u'/zones/batchrecordchanges') + u'?' + u'&'.join(args)

        response, data = self.__make_request(url, u'GET', self.headers, **kwargs)
        return ListBatchChangeSummaries.from_dict(data)

    def add_zone_acl_rule(self, zone_id, acl_rule, **kwargs):
        """
        Put an acl rule on the zone.

        :param zone_id: The id of the zone to attach the acl rule to
        :param acl_rule: The acl rule contents
        :return: the content of the response
        """
        url = urljoin(self.index_url, '/zones/{0}/acl/rules'.format(zone_id))
        response, data = self.__make_request(url, 'PUT', self.headers,
                                             to_json_string(acl_rule), **kwargs)

        return ZoneChange.from_dict(data)

    def delete_zone_acl_rule(self, zone_id, acl_rule, **kwargs):
        """
        Delete an acl rule from the zone.

        :param zone_id: The id of the zone to remove the acl from
        :param acl_rule: The acl rule to remove
        :return: the content of the response
        """
        url = urljoin(self.index_url, '/zones/{0}/acl/rules'.format(zone_id))
        response, data = self.__make_request(url, 'DELETE', self.headers,
                                             to_json_string(acl_rule), **kwargs)

        return ZoneChange.from_dict(data)
