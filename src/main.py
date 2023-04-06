import argparse

from src.config import is_invalid, is_sharing_enabled, load_config, replace_placeholder
from src.rds import (
    copy_snapshot,
    does_target_exists,
    init_client,
    restore_snapshot,
    share_snapshot,
)
from src.tf import get_outputs
from src.utils import assume_aws_role, setup_custom_logger

LOGGER = setup_custom_logger("root")


def main(command_line=None):
    parser = argparse.ArgumentParser(description="Restore RDS snapshot")
    parser.add_argument("-c", "--config", required=True)
    parser.add_argument("-t", "--tfstate")
    args = parser.parse_args(command_line)

    data = load_config(args.config)
    status = is_invalid(data)
    if status:
        LOGGER.error(status)
        exit(1)

    source = data["Source"]
    target = data["Target"]
    target_credentials = assume_aws_role(target["AssumeRole"], "target")
    source_share_credentials = assume_aws_role(source["Share"]["AssumeRole"], "source")

    tf_outputs = get_outputs(target_credentials, args.tfstate)
    if tf_outputs is None:
        LOGGER.error("TF state file does not exists")
        exit(1)

    source = replace_placeholder(source, tf_outputs, target_credentials)
    target = replace_placeholder(target, tf_outputs, target_credentials)

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
