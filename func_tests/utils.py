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

def wait_until_recordset_deleted(vinyldns_client, zone_id, rs_id):
    retries = MAX_RETRIES
    rs = vinyldns_client.get_record_set(zone_id, rs_id)
    delete_rs = vinyldns_client.delete_record_set(zone_id, rs_id)
    while (rs is not None) and retries > 0:
        rs = vinyldns_client.get_record_set(zone_id, rs_id)
        time.sleep(RETRY_WAIT)
        retries -= 1

    assert rs is None
