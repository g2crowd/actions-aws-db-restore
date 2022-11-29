import json
import logging
import os
import re

import boto3
import ssm
import tf
import rds

LOGGER = logging.getLogger("root")


def setup_custom_logger(name):
    formatter = logging.Formatter(fmt="[%(levelname)s] %(message)s")

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)
    return logger


def assume_aws_role(role):
    LOGGER.info("Assuming AWS role")
    client = boto3.client("sts")
    response = client.assume_role(RoleArn=role, RoleSessionName="RestoreDBSession")
    return response["Credentials"]


def get_tags(input):
    tags = []
    input = input.strip().split(",")

    for item in input:
        tag = {}
        item = item.split(":")
        if len(item) != 2:
            LOGGER.error("Invalid tags")
            exit(1)

        tag["Key"] = item[0]
        tag["Value"] = item[1]
        tags.append(tag)
    return tags


def validate_key(data, key, config_name):
    if data.get(key) is None:
        LOGGER.error("Invalid %s config, %s is not defined" % (config_name, key))
        exit(1)
    elif len(data[key]) == 0:
        LOGGER.error("Invalid %s config, %s is empty" % (config_name, key))
        exit(1)


def parse_config(value, tf_outputs, assume_role):
    if type(value) == str:
        pattern = re.compile(r"\${(.+):(.+)}")
        result = pattern.search(value)
        if result is None:
            return value
        if result.group(1) == "tf":
            if tf_outputs.get(result.group(2)) is None:
                LOGGER.error("%s does not exists in TF state" % result.group(2))
            value = tf_outputs[result.group(2)]
        elif result.group(1) == "ssm":
            value = ssm.get_parameter(assume_role, result.group(2))
        elif result.group(1) == "env":
            if os.environ.get(result.group(2)) is None:
                LOGGER.error(
                    "%s environment variable does not exists" % result.group(2)
                )
            value = os.environ[result.group(2)]
        return value
    elif type(value) == list:
        return [parse_config(i, tf_outputs, assume_role) for i in value]
    elif type(value) == dict:
        return {k: parse_config(i, tf_outputs, assume_role) for k, i in value.items()}
    return value
