import json
import logging
import os.path

import boto3
import ssm
import utils

LOGGER = logging.getLogger("root")


def load_source(data):
    utils.validate_key(data, "Source", "Source")
    utils.validate_key(data["Source"], "DBIdentifier", "DBIdentifier")
    if data["Source"].get("Share") is None:
        data["Source"]["ShareEnabled"] = False
    else:
        utils.validate_key(data["Source"]["Share"], "TargetAccount", "TargetAccount")
        utils.validate_key(data["Source"]["Share"], "KmsKey", "KmsKey")
        if data["Source"]["Share"].get("AssumeRole") is None:
            data["AssumeSourceRole"] = None
        else:
            data["AssumeSourceRole"] = utils.assume_aws_role(
                data["Source"]["Share"]["AssumeRole"]
            )
    return data


def load_target(data):
    utils.validate_key(data, "Target", "Target")
    utils.validate_key(data["Target"], "DBIdentifier", "DBIdentifier")

    if data["Target"].get("AssumeRole") is None:
        data["AssumeTargetRole"] = None
    else:
        data["AssumeTargetRole"] = utils.assume_aws_role(data["Target"]["AssumeRole"])

    utils.validate_key(data["Target"], "DBSubnetGroupName", "DBSubnetGroupName")
    utils.validate_key(data["Target"], "VpcSecurityGroupIds", "VpcSecurityGroupIds")
    utils.validate_key(data["Target"], "Tags", "Tags")
    utils.validate_key(data["Target"], "DBInstanceClass", "DBInstanceClass")

    if data["Target"].get("CopyTagsToSnapshot") is None:
        data["Target"]["CopyTagsToSnapshot"] = True
    if data["Target"].get("PubliclyAccessible") is None:
        data["Target"]["PubliclyAccessible"] = False
    if data["Target"].get("DeleteExistingTarget") is None:
        data["Target"]["DeleteExistingTarget"] = False

    return data


def load_config(filename):
    if not is_config_exists(filename):
        LOGGER.error("Provided configuration file is not available")
        exit(1)

    with open(filename) as file:
        data = json.load(file)

    if data.get("ClusterMode") is None:
        data["ClusterMode"] = True

    data = load_source(data)
    data = load_target(data)
    return data


def is_config_exists(filename):
    return os.path.isfile(filename)


def is_sharing_enabled(data):
    if data["Source"].get("Share") is None:
        return False
    return data["Source"]["Share"]
