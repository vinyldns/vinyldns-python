from func_test.vinyldns_context import *

def test_list_zones(vinyldns_test_context):
    zones = vinyldns_test_context.client.list_zones()
    assert 'maxItems' in zones
    assert 'zones' in zones
