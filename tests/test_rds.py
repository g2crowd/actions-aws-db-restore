import pytest
from moto import mock_rds
from src.rds import *

CLUSTER_MODE_DISABLED = False


@mock_rds
def init_conn():
    conn = boto3.client("rds", region_name="us-east-1")
    return conn


@mock_rds
def create_db(conn, db_id):
    conn.create_db_instance(
        DBInstanceIdentifier=db_id,
        AllocatedStorage=10,
        DBInstanceClass="postgres",
        Engine="db.m1.small",
        MasterUsername="root",
        MasterUserPassword="hunter2",
        Port=1234,
        DBSecurityGroups=["my_sg"],
    )
    instances = conn.describe_db_instances()
    return instances["DBInstances"]


def create_db_snapshots(conn, db_id, snapshot_id):
    create_db(conn, db_id)

    snapshot = conn.create_db_snapshot(
        DBInstanceIdentifier=db_id, DBSnapshotIdentifier=snapshot_id
    ).get("DBSnapshot")

    return snapshot


@mock_rds
def test_check_target():
    conn = init_conn()
    db_id = "master-db"
    create_db(conn, db_id)
    assert does_target_exists(conn, db_id, CLUSTER_MODE_DISABLED) == True


@mock_rds
def test_check_target_which_doesnt_exists():
    conn = init_conn()
    db_id = "master-db"
    assert does_target_exists(conn, db_id, CLUSTER_MODE_DISABLED) == False


@mock_rds
def test_get_latest_snapshot():
    conn = init_conn()
    db_id = "master-db"
    snapshot_id = "backup-1"
    snapshot = create_db_snapshots(conn, db_id, snapshot_id)
    assert get_latest_snapshot(conn, db_id, CLUSTER_MODE_DISABLED) != None


@mock_rds
def test_get_latest_snapshot_which_doesnt_exists():
    conn = init_conn()
    db_id = "master-db"
    create_db(conn, db_id)
    assert get_latest_snapshot(conn, db_id, CLUSTER_MODE_DISABLED) == None


@mock_rds
def test_delete_rds():
    conn = init_conn()
    db_id = "master-db"
    create_db(conn, db_id)
    assert delete_rds(conn, db_id, CLUSTER_MODE_DISABLED) == True


@mock_rds
def test_delete_rds_which_doesnt_exists():
    conn = init_conn()
    db_id = "master-db"
    assert delete_rds(conn, db_id, CLUSTER_MODE_DISABLED) == False


@mock_rds
def test_update_identifier():
    conn = init_conn()
    db_id = "master-db"
    new_db_id = "latest-master-db"
    create_db(conn, db_id)
    assert update_identifier(conn, db_id, new_db_id, CLUSTER_MODE_DISABLED) == True


@mock_rds
def test_update_identifier_which_doesnt_exists():
    conn = init_conn()
    db_id = "master-db"
    new_db_id = "latest-master-db"
    assert update_identifier(conn, db_id, new_db_id, CLUSTER_MODE_DISABLED) == False


@mock_rds
def test_copy_snapshot():
    conn = init_conn()
    db_id = "master-db"
    snapshot_id = "backup-1"
    new_snapshot_id = "latest-backup-1"
    create_db(conn, db_id)
    snapshot = create_db_snapshots(conn, db_id, snapshot_id)
    target_snapshot, target_snapshot_arn = copy_snapshot(
        conn, snapshot_id, new_snapshot_id, "alias/rds", CLUSTER_MODE_DISABLED
    )
    assert target_snapshot == new_snapshot_id


def test_copy_snapshot_which_doesnt_exists():
    conn = init_conn()
    db_id = "master-db"
    snapshot_id = "backup-1"
    new_snapshot_id = "latest-backup-1"
    assert copy_snapshot(
        conn, snapshot_id, new_snapshot_id, "alias/rds", CLUSTER_MODE_DISABLED
    ) == (None, None)
