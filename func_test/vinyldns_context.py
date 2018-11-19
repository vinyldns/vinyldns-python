import sys
sys.path.append('../')
sys.path.append('./')
import pytest
from src import *
from func_test.utils import *

class VinylDNSContext(object):
    """
    Creates the groups and zones needed for other tests
    """
    def __init__(self):
        self.client = client.VinylDNSClient("http://localhost:9000", "okAccessKey", "okSecretKey")
        self.tear_down()
        self.group = None

        group = {
            'name': 'vinyldns-python-test-group',
            'email': 'test@test.com',
            'description': 'this is a description',
            'members': [ { 'id': 'ok'} ],
            'admins': [ { 'id': 'ok'} ]
        }

        self.group = self.client.create_group(group)
        assert 'id' in self.group

        zone = {
            'name': 'vinyldns.',
            'email': 'test@test.com',
            'shared': False,
            'adminGroupId': self.group['id']
        }
        zone_change = self.client.create_zone(zone)
        print("!!!!!!!!!!CHANGE:\n")
        print(zone_change)
        assert 'zone' in zone_change
        self.zone = zone_change['zone']
        print("ZONE IS:::")
        print(self.zone)
        wait_until_zone_exists(self.client, self.zone['id'])


    # finalizer called by py.test when the simulation is torn down
    def tear_down(self):
        self.clear_zones()
        self.clear_groups()

    def clear_groups(self):
        groups = self.client.list_all_my_groups()
        for group in groups:
            self.client.delete_group(group['id'])
        print("FINAL GRPS")
        print(self.client.list_all_my_groups())

    def clear_zones(self):
        # Get the groups for the ok user
        groups = self.client.list_all_my_groups()
        group_ids = map(lambda x: x['id'], groups)

        zones = self.client.list_zones()['zones']

        # we only want to delete zones that the ok user "owns"
        zones_to_delete = filter(lambda x: (x['adminGroupId'] in group_ids), zones)

        zoneids_to_delete = map(lambda x: x['id'], zones_to_delete)

        for id in zoneids_to_delete:
            self.client.delete_zone(id)
            wait_until_zone_deleted(self.client, id)


@pytest.fixture(scope = "session")
def vinyldns_test_context(request):
    fix = VinylDNSContext()
    def fin():
        fix.tear_down()

    request.addfinalizer(fin)

    return fix
