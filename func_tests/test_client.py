from func_tests.vinyldns_context import vinyldns_test_context
from vinyldns.batch_change import AddRecordChange, DeleteRecordSetChange, BatchChange, BatchChangeRequest, \
    DeleteRecordSet, AddRecord, BatchChangeSummary, ListBatchChangeSummaries
from vinyldns.record import RecordSet, RecordType, AData, AAAAData, PTRData
from func_tests.utils import *

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


def test_batch_change_review_process_reject(vinyldns_test_context):
    changes = [
        AddRecord('test-approve-success.not.loaded.', RecordType.A, 200, AData("4.3.2.1"))
    ]

    bc = vinyldns_test_context.client.create_batch_change(
        BatchChangeRequest(changes, 'comments', vinyldns_test_context.group.id)
    )

    assert bc.status == 'PendingReview'
    assert bc.approval_status == 'PendingReview'
    assert len(bc.changes[0].validation_errors) == 1

    vinyldns_test_context.support_client.reject_batch_change(bc.id, 'cannot create the zone')

    completed_bc = vinyldns_test_context.client.get_batch_change(bc.id)

    assert completed_bc.status == 'Rejected'
    assert completed_bc.approval_status == 'ManuallyRejected'
    assert completed_bc.reviewer_id == 'support-user-id'
    assert completed_bc.reviewer_user_name == 'support-user'
    assert completed_bc.review_comment == 'cannot create the zone'


def test_batch_change_review_process_cancel(vinyldns_test_context):
    changes = [
        AddRecord('test-approve-success.not.loaded.', RecordType.A, 200,
                  AData("4.3.2.1"))
    ]

    bc = vinyldns_test_context.client.create_batch_change(
        BatchChangeRequest(changes, 'comments', vinyldns_test_context.group.id)
    )

    assert bc.status == 'PendingReview'
    assert bc.approval_status == 'PendingReview'
    assert len(bc.changes[0].validation_errors) == 1

    cancelled_bc = vinyldns_test_context.client.cancel_batch_change(bc.id)

    assert cancelled_bc.status == 'Cancelled'
    assert cancelled_bc.approval_status == 'Cancelled'


def test_batch_change_review_process_approve(vinyldns_test_context):
    approver = vinyldns_test_context.support_client

    changes = [
        AddRecord('test-approve-success.not.loaded.', RecordType.A, 200, AData("4.3.2.1"))
    ]

    bc = vinyldns_test_context.client.create_batch_change(
        BatchChangeRequest(changes, 'comments', vinyldns_test_context.group.id)
    )

    assert bc.status == 'PendingReview'
    assert bc.approval_status == 'PendingReview'
    assert len(bc.changes[0].validation_errors) == 1

    # need to create the zone so the change can succeed
    zone = {
        'name': 'not.loaded.',
        'email': 'test@test.com',
        'adminGroupId': vinyldns_test_context.group.id,
        'backendId': 'func-test-backend',
        'shared': True
    }
    zone_create = approver.connect_zone(zone)
    to_disconnect = zone_create.zone
    wait_until_zone_exists(approver, to_disconnect.id)

    vinyldns_test_context.support_client.approve_batch_change(bc.id, 'all good!')

    completed_bc = vinyldns_test_context.client.get_batch_change(bc.id)

    assert completed_bc.approval_status == 'ManuallyApproved'
    assert completed_bc.reviewer_id == 'support-user-id'
    assert completed_bc.reviewer_user_name == 'support-user'
    assert completed_bc.review_comment == 'all good!'

def test_list_abandoned_zones(vinyldns_test_context):
    vinyldns_test_context.clear_zones()
    list_abandoned_zones = vinyldns_test_context.client.list_abandoned_zones()
    assert len(list_abandoned_zones.deleted_zone_changes) > 0
    assert list_abandoned_zones.max_items > 0
    abandoned_zone = [x for x in list_abandoned_zones.deleted_zone_changes][0]    
    assert abandoned_zone is not None
    assert abandoned_zone.zone_changes.zone.name == vinyldns_test_context.zone.name
    assert abandoned_zone.zone_changes.zone.email == vinyldns_test_context.zone.email
    assert abandoned_zone.zone_changes.zone.admin_group_id == vinyldns_test_context.zone.admin_group_id
    assert abandoned_zone.zone_changes.zone.id is not None
    assert abandoned_zone.zone_changes.zone.created is not None
    assert abandoned_zone.zone_changes.zone.status == 'Deleted'
