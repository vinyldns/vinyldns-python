import sys
sys.path.append('../')
sys.path.append('./')
import pytest
from vinyldns.membership import Group, ListGroupsResponse, User
from vinyldns.zone import Zone
from vinyldns.client import VinylDNSClient
from func_tests.utils import *

class VinylDNSContext(object):
    """
    Creates the groups and zones needed for other tests
    """
    def __init__(self):
        self.client = VinylDNSClient("http://localhost:9000", "okAccessKey", "okSecretKey")
        self.group = None
        self.tear_down()

        group = Group(
            name='vinyldns-python-test-group',
            email='test@test.com',
            description='this is a description',
            members=[User(id='ok')],
            admins=[User(id='ok')]
        )

        self.group = self.client.create_group(group)

        zone = Zone(
            name='vinyldns.',
            email='test@test.com',
            admin_group_id=self.group.id
        )
        zone_change = self.client.connect_zone(zone)
        self.zone = zone_change.zone


        reverse_zone = Zone(
            name='2.0.192.in-addr.arpa.',
            email='test@test.com',
            admin_group_id=self.group.id
        )
        zone_change = self.client.connect_zone(reverse_zone)
        self.reverse_zone = zone_change.zone
        wait_until_zone_exists(self.client, self.reverse_zone.id)

    # finalizer called by py.test when the simulation is torn down
    def tear_down(self):
        self.clear_zones()
        self.clear_groups()

    def clear_groups(self):
        groups = self.client.list_all_my_groups().groups
        for group in groups:
            self.client.delete_group(group.id)

    def clear_zones(self):
        # Get the groups for the ok user
        groups = self.client.list_all_my_groups().groups
        group_ids = list(map(lambda x: x.id, groups))

        zones = self.client.list_zones().zones

        # we only want to delete zones that the ok user "owns"
        zones_to_delete = list(filter(lambda x: x.admin_group_id in group_ids, zones))
        for zone in zones_to_delete:
            print("Zone to delete %s" % zone.name)

        zoneids_to_delete = list(map(lambda x: x.id, zones_to_delete))

        for id in zoneids_to_delete:
            print("Going to abandon zone id %s" %id)
            self.client.abandon_zone(id)
            wait_until_zone_deleted(self.client, id)


@pytest.fixture(scope="session")
def vinyldns_test_context(request):
    fix = VinylDNSContext()
    def fin():
        fix.tear_down()

    request.addfinalizer(fin)

    return fix
