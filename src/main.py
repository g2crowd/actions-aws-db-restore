import argparse

from src.config import is_sharing_enabled, is_valid, load_config, replace_placeholder
from src.rds import copy_snapshot, does_target_exists, init_client, restore_snapshot, share_snapshot
from src.tf import get_outputs
from src.utils import assume_aws_role, setup_custom_logger

LOGGER = setup_custom_logger("root")


def main(command_line=None):
    parser = argparse.ArgumentParser(description="Restore RDS snapshot")
    parser.add_argument("-c", "--config", required=True)
    parser.add_argument("-t", "--tfstate")
    args = parser.parse_args(command_line)

    data = load_config(args.config)
    status = is_valid(data)
    if not status:
        exit(1)

    target_credentials = None
    if data["Target"].get("AssumeRole") is not None:
        LOGGER.info("Assuming target AWS role")
        target_credentials = assume_aws_role(data["Target"]["AssumeRole"])
    source_share_credentials = None
    if data["Source"]["Share"].get("AssumeRole") is not None:
        LOGGER.info("Assuming source AWS role")
        source_share_credentials = assume_aws_role(
            data["Source"]["Share"]["AssumeRole"]
        )

    tf_outputs = {}
    if args.tfstate is not None:
        tf_outputs = get_outputs(target_credentials, args.tfstate)
        if tf_outputs is None:
            LOGGER.error("TF state file does not exists")
            exit(1)
    data = replace_placeholder(data, tf_outputs, target_credentials)

    source = data["Source"]
    target = data["Target"]
    target_client = init_client(target_credentials)

    target_exists = does_target_exists(
        target_client, target["DBIdentifier"], data["ClusterMode"]
    )
    if target_exists and not data["DeleteExistingTarget"]:
        LOGGER.error("Target DB already exists and target DB deletion is disabled")
        exit(1)

    if is_sharing_enabled(source):
        source_client = init_client(source_share_credentials)
        target["SnapshotIdentifier"], target["SnapshotArn"] = share_snapshot(
            source_client,
            source["DBIdentifier"],
            target["DBIdentifier"],
            source["Share"]["SourceKmsKey"],
            source["Share"]["TargetAccount"],
            data["ClusterMode"],
        )
        if target["SnapshotIdentifier"] is None:
            return

        LOGGER.info(
            "Updating KMS key of {} with {}".format(
                target["SnapshotArn"], source["Share"]["TargetKmsKey"]
            )
        )
        target["SnapshotIdentifier"], target["SnapshotArn"] = copy_snapshot(
            target_client,
            target["SnapshotArn"],
            target["SnapshotIdentifier"],
            source["Share"]["TargetKmsKey"],
            data["ClusterMode"],
        )

    restore_snapshot(target_client, target, target_exists, data["ClusterMode"])


if __name__ == "__main__":
    main()
