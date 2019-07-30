from func_tests.vinyldns_context import vinyldns_test_context
from vinyldns.batch_change import AddRecordChange, DeleteRecordSetChange, BatchChange, BatchChangeRequest, \
    DeleteRecordSet, AddRecord, BatchChangeSummary, ListBatchChangeSummaries, RejectBatchChangeRequest
from vinyldns.record import RecordSet, RecordType, AData, AAAAData, PTRData
from func_tests.utils import wait_until_record_set_exists, wait_until_recordset_deleted


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

    rs = change.record_set
    wait_until_record_set_exists(vinyldns_test_context.client, rs.zone_id, rs.id)

    r = vinyldns_test_context.client.get_record_set(rs.zone_id, rs.id)
    assert r.id == rs.id
    assert r.name == rs.name
    assert r.ttl == rs.ttl
    assert all([l.__dict__ == r.__dict__ for l, r in zip(rs.records, r.records)])

    wait_until_recordset_deleted(vinyldns_test_context.client, rs.zone_id, rs.id)


def test_create_batch_change(vinyldns_test_context):
    changes = [
        AddRecord('change-test.vinyldns.', RecordType.A, 200, AData('192.0.2.111')),
        AddRecord('192.0.2.111', RecordType.PTR, 200, PTRData('change-test.vinyldns.'))
    ]
    r = vinyldns_test_context.client.create_batch_change(
        BatchChangeRequest(changes, 'comments', vinyldns_test_context.group.id)
    )
    assert r.user_id == 'ok'
    assert r.user_name == 'ok'
    assert r.comments == 'comments'
    assert r.approval_status == 'AutoApproved'

    change1 = r.changes[0]
    assert change1.input_name == 'change-test.vinyldns.'
    assert change1.ttl == 200
    assert change1.record.address == '192.0.2.111'
    assert change1.type == RecordType.A

    change2 = r.changes[1]
    assert change2.input_name == '192.0.2.111'
    assert change2.ttl == 200
    assert change2.record.ptrdname == 'change-test.vinyldns.'
    assert change2.type == RecordType.PTR

    wait_until_recordset_deleted(vinyldns_test_context.client, r.changes[0].zone_id, r.changes[0].record_set_id)
    wait_until_recordset_deleted(vinyldns_test_context.client, r.changes[1].zone_id, r.changes[1].record_set_id)


def test_batch_change_review_process(vinyldns_test_context):
    changes = [
        AddRecord('test-approve-success.not.loaded.', RecordType.A, 200, AData("4.3.2.1"))
    ]

    bc = vinyldns_test_context.client.create_batch_change(
        BatchChangeRequest(changes, 'comments', vinyldns_test_context.group.id)
    )

    assert bc.status == 'PendingReview'
    assert bc.approval_status == 'PendingReview'
    assert len(bc.changes[0].validation_errors) == 1

    rejection = RejectBatchChangeRequest(review_comment='cannot create the zone')

    approve_bc = vinyldns_test_context.support_client.reject_batch_change(bc.id, rejection)

    completed_bc = vinyldns_test_context.client.get_batch_change(bc.id)

    assert completed_bc.status == 'Rejected'
    assert completed_bc.approval_status == 'ManuallyRejected'
    assert completed_bc.reviewer_id == 'support-user-id'
    assert completed_bc.reviewer_username == 'support-user'
    assert completed_bc.review_comment == 'cannot create the zone'
