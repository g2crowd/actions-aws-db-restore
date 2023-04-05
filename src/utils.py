import logging

import boto3

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
