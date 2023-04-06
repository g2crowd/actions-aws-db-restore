import logging

import boto3
from botocore.exceptions import ClientError

LOGGER = logging.getLogger("root")


def init_client(assumed_role):
    if assumed_role is None:
        client = boto3.client("ssm")
    else:
        client = boto3.client(
            "ssm",
            aws_access_key_id=assumed_role["AccessKeyId"],
            aws_secret_access_key=assumed_role["SecretAccessKey"],
            aws_session_token=assumed_role["SessionToken"],
        )
    return client


def get_parameter(assumed_role, name):
    client = init_client(assumed_role)
    try:
        result = client.get_parameter(Name=name, WithDecryption=True)
    except ClientError as err:
        LOGGER.error(
            "{}: {}".format(
                err.response["Error"]["Code"], err.response["Error"]["Message"]
            )
        )
        return None

    return result["Parameter"]["Value"]
