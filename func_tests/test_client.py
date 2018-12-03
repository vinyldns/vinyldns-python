from func_tests.vinyldns_context import vinyldns_test_context

def test_list_zones(vinyldns_test_context):
    zones = vinyldns_test_context.client.list_zones()
    assert 'maxItems' in zones
    assert 'zones' in zones
