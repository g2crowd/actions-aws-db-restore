import logging
from datetime import datetime
from operator import itemgetter

import boto3
from botocore.exceptions import ClientError

LOGGER = logging.getLogger("root")


def init_client(assumed_role):
    if assumed_role is None:
        client = boto3.client("rds")
    else:
        client = boto3.client(
            "rds",
            aws_access_key_id=assumed_role["AccessKeyId"],
            aws_secret_access_key=assumed_role["SecretAccessKey"],
            aws_session_token=assumed_role["SessionToken"],
        )
    return client


def does_target_exists(client, db_identifier, cluster_mode):
    if cluster_mode:
        response = client.describe_db_clusters(
            Filters=[{"Name": "db-cluster-id", "Values": [db_identifier]}]
        )
        if len(response["DBClusters"]) == 0:
            return False

    else:
        response = client.describe_db_instances(
            Filters=[{"Name": "db-instance-id", "Values": [db_identifier]}]
        )
        if len(response["DBInstances"]) == 0:
            return False
    return True


def get_latest_snapshot(client, db_identifier, cluster_mode):
    if cluster_mode:
        response = client.describe_db_cluster_snapshots(
            DBClusterIdentifier=db_identifier, SnapshotType="automated"
        )
        if not response["DBClusterSnapshots"]:
            return None
        sorted_keys = sorted(
            response["DBClusterSnapshots"],
            key=itemgetter("SnapshotCreateTime"),
            reverse=True,
        )
        snapshot_arn = sorted_keys[0]["DBClusterSnapshotArn"]
    else:
        response = client.describe_db_snapshots(
            DBInstanceIdentifier=db_identifier, SnapshotType="automated"
        )
        if not response["DBSnapshots"]:
            return None
        sorted_keys = sorted(
            response["DBSnapshots"], key=itemgetter("SnapshotCreateTime"), reverse=True
        )
        snapshot_arn = sorted_keys[0]["DBSnapshotArn"]
    return snapshot_arn


def delete_rds(client, db_identifier, cluster_mode):
    LOGGER.info("Deleting %s db" % db_identifier)
    try:
        if cluster_mode:
            client.delete_db_cluster(
                DBClusterIdentifier=db_identifier, SkipFinalSnapshot=True
            )
            waiter = client.get_waiter("db_cluster_deleted")
            waiter.wait(DBClusterIdentifier=db_identifier)
        else:
            client.delete_db_instance(
                DBInstanceIdentifier=db_identifier,
                SkipFinalSnapshot=True,
                DeleteAutomatedBackups=True,
            )
            waiter = client.get_waiter("db_instance_deleted")
            waiter.wait(DBInstanceIdentifier=db_identifier)
    except ClientError as err:
        LOGGER.error(
            "{}: {}".format(
                err.response["Error"]["Code"], err.response["Error"]["Message"]
            )
        )
        return False
    return True


def update_identifier(client, source, target, cluster_mode):
    LOGGER.info("Modifying DB identifier {} to {}".format(source, target))
    try:
        if cluster_mode:
            client.modify_db_cluster(
                DBClusterIdentifier=source,
                NewDBClusterIdentifier=target,
                ApplyImmediately=True,
            )
        else:
            client.modify_db_instance(
                DBInstanceIdentifier=source,
                NewDBInstanceIdentifier=target,
                ApplyImmediately=True,
            )
    except ClientError as err:
        LOGGER.error(
            "{}: {}".format(
                err.response["Error"]["Code"], err.response["Error"]["Message"]
            )
        )
        return False
    return True


def copy_snapshot(client, source, target, kms_key, cluster_mode):
    try:
        if cluster_mode:
            response = client.copy_db_cluster_snapshot(
                SourceDBClusterSnapshotIdentifier=source,
                TargetDBClusterSnapshotIdentifier=target,
                KmsKeyId=kms_key,
            )
            target_snapshot = response["DBClusterSnapshot"][
                "DBClusterSnapshotIdentifier"
            ]
            target_snapshot_arn = response["DBClusterSnapshot"]["DBClusterSnapshotArn"]
            waiter = client.get_waiter("db_cluster_snapshot_available")
            waiter.wait(DBClusterSnapshotIdentifier=target_snapshot_arn)

        else:
            response = client.copy_db_snapshot(
                SourceDBSnapshotIdentifier=source,
                TargetDBSnapshotIdentifier=target,
                KmsKeyId=kms_key,
            )
            target_snapshot = response["DBSnapshot"]["DBSnapshotIdentifier"]
            target_snapshot_arn = response["DBSnapshot"]["DBSnapshotArn"]
            waiter = client.get_waiter("db_snapshot_available")
            waiter.wait(DBSnapshotIdentifier=target_snapshot)
    except ClientError as err:
        LOGGER.error(
            "{}: {}".format(
                err.response["Error"]["Code"], err.response["Error"]["Message"]
            )
        )
        return None, None

    return target_snapshot, target_snapshot_arn


def share_snapshot(client, source, target, kms_key, account, cluster_mode):
    source_snapshot_arn = get_latest_snapshot(client, source, cluster_mode)
    if source_snapshot_arn is None:
        LOGGER.error("Failed to get latest DB snapshot")
        return None, None
    now = datetime.now()
    target = target + "-" + now.strftime("%d%M%S")
    LOGGER.info(
        "Updating KMS key of snapshot {} with {}".format(source_snapshot_arn, kms_key)
    )
    target_snapshot, target_snapshot_arn = copy_snapshot(
        client, source_snapshot_arn, target, kms_key, cluster_mode
    )
    if target_snapshot is None:
        return target_snapshot, target_snapshot_arn

    LOGGER.info("Sharing snapshot {} with {}".format(target_snapshot_arn, account))
    if cluster_mode:
        client.modify_db_cluster_snapshot_attribute(
            DBClusterSnapshotIdentifier=target_snapshot,
            AttributeName="restore",
            ValuesToAdd=[account],
        )
    else:
        client.modify_db_snapshot_attribute(
            DBSnapshotIdentifier=target_snapshot,
            AttributeName="restore",
            ValuesToAdd=[account],
        )

    return target_snapshot, target_snapshot_arn


def restore_snapshot(client, data, target_exists, cluster_mode):
    db_identifier = data["DBIdentifier"]
    if target_exists:
        db_identifier = data["SnapshotIdentifier"]

    LOGGER.info("Creating RDS {} from {}".format(db_identifier, data["SnapshotArn"]))
    if cluster_mode:
        client.restore_db_cluster_from_snapshot(
            DBClusterIdentifier=db_identifier,
            SnapshotIdentifier=data["SnapshotArn"],
            DBClusterInstanceClass=data["DBInstanceClass"],
            DBSubnetGroupName=data["DBSubnetGroupName"],
            VpcSecurityGroupIds=data["VpcSecurityGroupIds"],
            Tags=data["Tags"],
            DeletionProtection=False,
            CopyTagsToSnapshot=True,
            PubliclyAccessible=data["PubliclyAccessible"],
        )
        waiter = client.get_waiter("db_cluster_available")
        waiter.wait(DBClusterIdentifier=db_identifier)
    else:
        client.restore_db_instance_from_db_snapshot(
            DBInstanceIdentifier=db_identifier,
            DBSnapshotIdentifier=data["SnapshotArn"],
            DBInstanceClass=data["DBInstanceClass"],
            DBSubnetGroupName=data["DBSubnetGroupName"],
            PubliclyAccessible=data["PubliclyAccessible"],
            Tags=data["Tags"],
            VpcSecurityGroupIds=data["VpcSecurityGroupIds"],
            CopyTagsToSnapshot=True,
            DeletionProtection=False,
        )
        waiter = client.get_waiter("db_instance_available")
        waiter.wait(DBInstanceIdentifier=db_identifier)

    if target_exists:
        delete_rds(client, data["DBIdentifier"], cluster_mode)
        update_identifier(client, db_identifier, data["DBIdentifier"], cluster_mode)
