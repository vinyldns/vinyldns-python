from func_tests.vinyldns_context import vinyldns_test_context
from vinyldns.record import RecordSet, RecordType, AData


def test_list_zones(vinyldns_test_context):
    list_zones = vinyldns_test_context.client.list_zones()
    assert len(list_zones.zones) > 0
    assert list_zones.max_items > 0
    zone = [x for x in list_zones.zones if x.name == vinyldns_test_context.zone.name][0]
    assert zone is not None
    assert zone.name == vinyldns_test_context.zone.name
    assert zone.email == vinyldns_test_context.zone.email
    assert zone.admin_group_id == vinyldns_test_context.zone.admin_group_id
    assert zone.id is not None
    assert zone.created is not None


def test_list_groups(vinyldns_test_context):
    list_groups = vinyldns_test_context.client.list_my_groups()
    assert len(list_groups.groups) > 0
    group = [x for x in list_groups.groups if x.name == vinyldns_test_context.group.name][0]
    assert group is not None
    assert group.name == vinyldns_test_context.group.name
    assert group.email == vinyldns_test_context.group.email
    assert group.description == vinyldns_test_context.group.description
    assert group.members[0].id == vinyldns_test_context.group.members[0].id
    assert group.admins[0].id == vinyldns_test_context.group.admins[0].id


def test_record_sets(vinyldns_test_context):
    rs = RecordSet(vinyldns_test_context.zone.id, 'a-test', RecordType.A, 200, records=[AData('1.2.3.4')])
    change = vinyldns_test_context.client.create_record_set(rs)
    assert change.record_set.zone_id == rs.zone_id
    assert change.record_set.type == rs.type
    assert change.record_set.ttl == rs.ttl
    assert change.record_set.name == rs.name
    assert all([l.__dict__ == r.__dict__ for l, r in zip(change.record_set.records, rs.records)])

