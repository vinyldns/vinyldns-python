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

import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

# TODO: Didn't like this boto request signer, fix when moving back
from src.boto_request_signer import BotoRequestSigner

# Python 2/3 compatibility
from requests.compat import urljoin, urlparse, urlsplit
from builtins import str
from future.utils import iteritems
from future.moves.urllib.parse import parse_qs

try:
    basestring
except NameError:
    basestring = str

logger = logging.getLogger(__name__)

__all__ = [u'VinylDNSClient', u'MAX_RETRIES', u'RETRY_WAIT']

MAX_RETRIES = 30
RETRY_WAIT = 0.05


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
        self.session_not_found_ok = self.__requests_retry_not_found_ok_session()

    @classmethod
    def from_env(cls):
        """
        Create client from environtment variables.

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

    def __requests_retry_not_found_ok_session(self,
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

    def __make_request(self, url, method=u'GET', headers=None, body_string=None,
                       sign_request=True, not_found_ok=False, **kwargs):

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

        if sign_request:
            signed_headers, signed_body = self.__build_vinyldns_request(method, path, body_string, query,
                                                                        with_headers=headers or {}, **kwargs)
        else:
            signed_headers = headers or {}
            signed_body = body_string

        if not_found_ok:
            response = self.session_not_found_ok.request(method, url, data=signed_body,
                                                         headers=signed_headers, **kwargs)
        else:
            response = self.session.request(method, url, data=signed_body, headers=signed_headers, **kwargs)

        try:
            return response.status_code, response.json()
        except Exception:
            return response.status_code, response.text

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

    def ping(self):
        """
        Perform a simple ping request.

        :return: the content of the response, which should be PONG
        """
        url = urljoin(self.index_url, '/ping')

        response, data = self.__make_request(url)
        return data

    def get_status(self):
        """
        Get processing status.

        :return: the content of the response
        """
        url = urljoin(self.index_url, '/status')

        response, data = self.__make_request(url)

        return data

    def post_status(self, status):
        """
        Update processing status.

        :return: the content of the response
        """
        url = urljoin(self.index_url, '/status?processingDisabled={}'.format(status))
        response, data = self.__make_request(url, 'POST', self.headers)

        return data

    def color(self):
        """
        Get the current color for the application.

        :return: the content of the response, which should be "blue" or "green"
        """
        url = urljoin(self.index_url, '/color')
        response, data = self.__make_request(url)
        return data

    def health(self):
        """
        Check the health of the app.

        Asserts that a 200 should be returned, otherwise this will fail.
        """
        url = urljoin(self.index_url, '/health')
        self.__make_request(url, sign_request=False)

    def create_group(self, group, **kwargs):
        """
        Create a new group.

        :param group: A group dictionary that can be serialized to json
        :return: the content of the response, which should be a group json
        """
        url = urljoin(self.index_url, u'/groups')
        response, data = self.__make_request(url, u'POST', self.headers, json.dumps(group), **kwargs)

        return data

    def get_group(self, group_id, **kwargs):
        """
        Get a group.

        :param group_id: Id of the group to get
        :return: the group json
        """
        url = urljoin(self.index_url, u'/groups/' + group_id)
        response, data = self.__make_request(url, u'GET', self.headers, **kwargs)

        return data

    def delete_group(self, group_id, **kwargs):
        """
        Delete a group.

        :param group_id: Id of the group to delete
        :return: the group json
        """
        url = urljoin(self.index_url, u'/groups/' + group_id)
        response, data = self.__make_request(url, u'DELETE', self.headers, not_found_ok=True, **kwargs)

        return data

    def update_group(self, group_id, group, **kwargs):
        """
        Update an existing group.

        :param group_id: The id of the group being updated
        :param group: A group dictionary that can be serialized to json
        :return: the content of the response, which should be a group json
        """
        url = urljoin(self.index_url, u'/groups/{0}'.format(group_id))
        response, data = self.__make_request(url, u'PUT', self.headers, json.dumps(group), not_found_ok=True, **kwargs)

        return data

    def list_my_groups(self, group_name_filter=None, start_from=None, max_items=None, **kwargs):
        """
        Retrieve my groups.

        :param start_from: the start key of the page
        :param max_items: the page limit
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

        return data

    def list_all_my_groups(self, group_name_filter=None, **kwargs):
        """
        Retrieve all my groups.

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

        while u'nextId' in data:
            args = []

            if group_name_filter:
                args.append(u'groupNameFilter={0}'.format(group_name_filter))
            if u'nextId' in data:
                args.append(u'startFrom={0}'.format(data[u'nextId']))

            response, data = self.__make_request(url, u'GET', self.headers, **kwargs)
            groups.extend(data[u'groups'])

        return groups

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

        response, data = self.__make_request(url, u'GET', self.headers, not_found_ok=True, **kwargs)

        return data

    def list_group_admins(self, group_id, **kwargs):
        """
        Return the group admins.

        :param group_id: the Id of the group
        :return: the user info of the admins
        """
        url = urljoin(self.index_url, u'/groups/{0}/admins'.format(group_id))
        response, data = self.__make_request(url, u'GET', self.headers, not_found_ok=True, **kwargs)

        return data

    def get_group_changes(self, group_id, start_from=None, max_items=None, **kwargs):
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

        return data

    def create_zone(self, zone, **kwargs):
        """
        Create a new zone with the given name and email.

        :param zone: the zone to be created
        :return: the content of the response
        """
        url = urljoin(self.index_url, u'/zones')
        response, data = self.__make_request(url, u'POST', self.headers, json.dumps(zone), **kwargs)
        return data

    def update_zone(self, zone, **kwargs):
        """
        Update a zone.

        :param zone: the zone to be created
        :return: the content of the response
        """
        url = urljoin(self.index_url, u'/zones/{0}'.format(zone[u'id']))
        response, data = self.__make_request(url, u'PUT', self.headers, json.dumps(zone), not_found_ok=True, **kwargs)
        return data

    def sync_zone(self, zone_id, **kwargs):
        """
        Sync a zone.

        :param zone: the zone to be updated
        :return: the content of the response
        """
        url = urljoin(self.index_url, u'/zones/{0}/sync'.format(zone_id))
        response, data = self.__make_request(url, u'POST', self.headers, not_found_ok=True, **kwargs)

        return data

    def delete_zone(self, zone_id, **kwargs):
        """
        Delete the zone for the given id.

        :param zone_id: the id of the zone to be deleted
        :return: nothing, will fail if the status code was not expected
        """
        url = urljoin(self.index_url, u'/zones/{0}'.format(zone_id))
        response, data = self.__make_request(url, u'DELETE', self.headers, not_found_ok=True, **kwargs)

        return data

    def get_zone(self, zone_id, **kwargs):
        """
        Get a zone for the given zone id.

        :param zone_id: the id of the zone to retrieve
        :return: the zone, or will 404 if not found
        """
        url = urljoin(self.index_url, u'/zones/{0}'.format(zone_id))
        response, data = self.__make_request(url, u'GET', self.headers, not_found_ok=True, **kwargs)

        return data

    def get_zone_history(self, zone_id, **kwargs):
        """
        Get the zone history for the given zone id.

        :param zone_id: the id of the zone to retrieve
        :return: the zone, or will 404 if not found
        """
        url = urljoin(self.index_url, u'/zones/{0}/history'.format(zone_id))

        response, data = self.__make_request(url, u'GET', self.headers, not_found_ok=True, **kwargs)
        return data

    def get_zone_change(self, zone_change, **kwargs):
        """
        Get a zone change with the provided id.

        Unfortunately, there is no endpoint, so we have to get all zone history and parse.
        """
        zone_change_id = zone_change[u'id']
        change = None

        def change_id_match(possible_match):
            return possible_match[u'id'] == zone_change_id

        history = self.get_zone_history(zone_change[u'zone'][u'id'])
        if u'zoneChanges' in history:
            zone_changes = history[u'zoneChanges']
            matching_changes = filter(change_id_match, zone_changes)

            if len(matching_changes) > 0:
                change = matching_changes[0]

        return change

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

        response, data = self.__make_request(url, u'GET', self.headers, not_found_ok=True, **kwargs)
        return data

    def list_recordset_changes(self, zone_id, start_from=None, max_items=None, **kwargs):
        """
        Get the recordset changes for the given zone id.

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

        response, data = self.__make_request(url, u'GET', self.headers, not_found_ok=True, **kwargs)
        return data

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
        return data

    def create_recordset(self, recordset, **kwargs):
        """
        Create a new recordset.

        :param recordset: the recordset to be created
        :return: the content of the response
        """
        if recordset and u'name' in recordset:
            recordset[u'name'] = recordset[u'name'].replace(u'_', u'-')

        url = urljoin(self.index_url, u'/zones/{0}/recordsets'.format(recordset[u'zoneId']))
        response, data = self.__make_request(url, u'POST', self.headers, json.dumps(recordset), **kwargs)
        return data

    def delete_recordset(self, zone_id, rs_id, **kwargs):
        """
        Delete an existing recordset.

        :param zone_id: the zone id the recordset belongs to
        :param rs_id: the id of the recordset to be deleted
        :return: the content of the response
        """
        url = urljoin(self.index_url, u'/zones/{0}/recordsets/{1}'.format(zone_id, rs_id))

        response, data = self.__make_request(url, u'DELETE', self.headers, not_found_ok=True, **kwargs)
        return data

    def update_recordset(self, recordset, **kwargs):
        """
        Delete an existing recordset.

        :param recordset: the recordset to be updated
        :return: the content of the response
        """
        url = urljoin(self.index_url, u'/zones/{0}/recordsets/{1}'.format(recordset[u'zoneId'], recordset[u'id']))

        response, data = self.__make_request(url, u'PUT', self.headers,
                                             json.dumps(recordset), not_found_ok=True, **kwargs)

        return data

    def get_recordset(self, zone_id, rs_id, **kwargs):
        """
        Get an existing recordset.

        :param zone_id: the zone id the recordset belongs to
        :param rs_id: the id of the recordset to be retrieved
        :return: the content of the response
        """
        url = urljoin(self.index_url, u'/zones/{0}/recordsets/{1}'.format(zone_id, rs_id))

        response, data = self.__make_request(url, u'GET', self.headers, None, not_found_ok=True, **kwargs)
        return data

    def get_recordset_change(self, zone_id, rs_id, change_id, **kwargs):
        """
        Get an existing recordset change.

        :param zone_id: the zone id the recordset belongs to
        :param rs_id: the id of the recordset to be retrieved
        :param change_id: the id of the change to be retrieved
        :return: the content of the response
        """
        url = urljoin(self.index_url, u'/zones/{0}/recordsets/{1}/changes/{2}'.format(zone_id, rs_id, change_id))

        response, data = self.__make_request(url, u'GET', self.headers, None, not_found_ok=True, **kwargs)
        return data

    def list_recordsets(self, zone_id, start_from=None, max_items=None, record_name_filter=None, **kwargs):
        """
        Retrieve all recordsets in a zone.

        :param zone_id: the zone to retrieve
        :param start_from: the start key of the page
        :param max_items: the page limit
        :param record_name_filter: only returns recordsets whose names contain filter string
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
        return data

    def create_batch_change(self, batch_change_input, **kwargs):
        """
        Create a new batch change.

        :param batch_change_input: the batchchange to be created
        :return: the content of the response
        """
        url = urljoin(self.index_url, u'/zones/batchrecordchanges')
        response, data = self.__make_request(url, u'POST', self.headers, json.dumps(batch_change_input), **kwargs)
        return data

    def get_batch_change(self, batch_change_id, **kwargs):
        """
        Get an existing batch change.

        :param batch_change_id: the unique identifier of the batchchange
        :return: the content of the response
        """
        url = urljoin(self.index_url, u'/zones/batchrecordchanges/{0}'.format(batch_change_id))
        response, data = self.__make_request(url, u'GET', self.headers, None, not_found_ok=True, **kwargs)
        return data

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
        return data

    def add_zone_acl_rule(self, zone_id, acl_rule, sign_request=True, **kwargs):
        """
        Put an acl rule on the zone.

        :param zone_id: The id of the zone to attach the acl rule to
        :param acl_rule: The acl rule contents
        :param sign_request: An indicator if we should sign the request; useful for testing auth
        :return: the content of the response
        """
        url = urljoin(self.index_url, '/zones/{0}/acl/rules'.format(zone_id))
        response, data = self.__make_request(url, 'PUT', self.headers,
                                             json.dumps(acl_rule), sign_request=sign_request, **kwargs)

        return data

    def delete_zone_acl_rule(self, zone_id, acl_rule, sign_request=True, **kwargs):
        """
        Delete an acl rule from the zone.

        :param zone_id: The id of the zone to remove the acl from
        :param acl_rule: The acl rule to remove
        :param sign_request:  An indicator if we should sign the request; useful for testing auth
        :return: the content of the response
        """
        url = urljoin(self.index_url, '/zones/{0}/acl/rules'.format(zone_id))
        response, data = self.__make_request(url, 'DELETE', self.headers,
                                             json.dumps(acl_rule), sign_request=sign_request, **kwargs)

        return data
