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

    if zone is None:
        print("Issue on zone create: {}".format(json.dumps(zone)))

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

    if zone is not None:
        print("Zone was not deleted: {}".format(json.dumps(zone)))

    assert zone is None
