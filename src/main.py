import argparse
import os

import rds
import tf
import utils
import config

LOGGER = utils.setup_custom_logger("root")


def main(command_line=None):
    parser = argparse.ArgumentParser(description="Restore RDS snapshot")
    parser.add_argument("-c", "--config", required=True)
    parser.add_argument("-o", "--override", action="store_true")
    parser.add_argument("-t", "--tfstate")
    args = parser.parse_args(command_line)

    data = config.load_config(args.config)
    tf_outputs = {}
    if args.tfstate is not None:
        tf_outputs = tf.get_outputs(data["AssumeTargetRole"], args.tfstate)
    data = utils.parse_config(data, tf_outputs, data["AssumeTargetRole"])

    target_exists = rds.does_target_exists(
        data["AssumeTargetRole"], data["Target"]["DBIdentifier"], data["ClusterMode"]
    )
    if target_exists and not args.override:
        LOGGER.error("Target DB already exists and target DB deletion is disabled")
        exit(1)

    if config.is_sharing_enabled(data):
        data["Target"]["SnapshotIdentifier"] = rds.share_snapshot(
            data["AssumeSourceRole"],
            data["Source"]["DBIdentifier"],
            data["Target"]["DBIdentifier"],
            data["Source"]["Share"]["KmsKey"],
            data["Source"]["Share"]["TargetAccount"],
            data["ClusterMode"],
        )

    print(data["Target"])
    # rds.restore_snapshot(data['Target'], target_exists, data['ClusterMode'])


if __name__ == "__main__":
    main()
