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
import json
import time
import logging
import collections

MAX_RETRIES = 30
RETRY_WAIT = 0.1

def wait_until_zone_exists(vinyldns_client, zone_id):
    """
    Waits until the zone exists
    """
    zone = vinyldns_client.get_zone(zone_id)
    retries = MAX_RETRIES
    while (zone is None) and retries > 0:
        zone = vinyldns_client.get_zone(zone_id)
        time.sleep(RETRY_WAIT)
        retries -= 1

    assert zone is not None


def wait_until_zone_deleted(vinyldns_client, zone_id):
    """
    Waits until the zone no longer exists
    """
    zone = vinyldns_client.get_zone(zone_id)
    retries = MAX_RETRIES
    while (zone is not None) and retries > 0:
        zone = vinyldns_client.get_zone(zone_id)
        time.sleep(RETRY_WAIT)
        retries -= 1

    assert zone is None


def wait_until_record_set_exists(vinyldns_client, zone_id, rs_id):
    """
    Waits until the zone exists
    """
    rs = vinyldns_client.get_record_set(zone_id, rs_id)
    retries = MAX_RETRIES
    while (rs is None) and retries > 0:
        rs = vinyldns_client.get_record_set(zone_id, rs_id)
        time.sleep(RETRY_WAIT)
        retries -= 1

    assert rs is not None
