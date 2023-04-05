import json
import logging
import os.path
import re
import secrets
import string

import jsonschema
from src.ssm import get_parameter

LOGGER = logging.getLogger("root")


def generate_password():
    alphabet = string.ascii_letters + string.digits
    password = "".join(secrets.choice(alphabet) for i in range(20))
    return password


def is_valid(data):
    schema = load_config("schema/config.json")
    try:
        jsonschema.validate(data, schema)
    except jsonschema.exceptions.ValidationError as err:
        print(err)
        return False
    return True


def load_config(filename):
    if not is_config_exists(filename):
        LOGGER.error("Provided configuration file is not available")
        exit(1)

    with open(filename) as file:
        data = json.load(file)

    return data


def is_config_exists(filename):
    return os.path.isfile(filename)


def is_sharing_enabled(data):
    if data.get("Share") is None:
        return False
    return data["Share"]


def fetch_from_tfstate(result, tf_outputs):
    if tf_outputs.get(result.group(2)) is None:
        LOGGER.error("%s does not exists in TF state" % result.group(2))

    return tf_outputs[result.group(2)]


def fetch_from_env(result):
    if os.environ.get(result.group(2)) is None:
        LOGGER.error("%s environment variable does not exists" % result.group(2))
    return os.environ[result.group(2)]


def fetch_from_ssm(result, assume_role):
    return get_parameter(assume_role, result.group(2))


def replace_placeholder(value, tf_outputs, assume_role):
    if type(value) == str:
        pattern = re.compile(r"\${(.+):(.+)}")
        result = pattern.search(value)
        if result is None:
            return value
        elif result.group(1) == "tf":
            value = fetch_from_tfstate(result, tf_outputs)
        elif result.group(1) == "ssm":
            value = fetch_from_ssm(result, assume_role)
        elif result.group(1) == "env":
            value = fetch_from_env(result)
        return value
    elif type(value) == list:
        return [replace_placeholder(i, tf_outputs, assume_role) for i in value]
    elif type(value) == dict:
        return {
            k: replace_placeholder(i, tf_outputs, assume_role) for k, i in value.items()
        }
    return value
