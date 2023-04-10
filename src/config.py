import json
import logging
import os.path
import re
import secrets
import string

import jsonschema
from src.ssm import get_parameter

LOGGER = logging.getLogger("root")


def schema_dir():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + "/schema/"


def is_invalid(data):
    if data is None:
        return True

    schema = load_config(schema_dir() + "config.json")
    try:
        jsonschema.validate(data, schema)
    except jsonschema.exceptions.ValidationError as err:
        return err
    return False


def load_config(filename):
    if not is_config_exists(filename):
        LOGGER.error("Provided configuration file is not available")
        return None

    with open(filename) as file:
        data = json.load(file)

    return data


def is_config_exists(filename):
    return os.path.isfile(filename)


def is_sharing_enabled(data):
    if data.get("Share") is None:
        return False
    return data["Share"]


def _fetch_from_tfstate(key, tf_outputs):
    if tf_outputs.get(key) is None:
        LOGGER.error("%s does not exists in TF state" % key)
        return None
    return tf_outputs[key]


def _fetch_from_env(key):
    if os.environ.get(key) is None:
        LOGGER.error("%s environment variable does not exists" % key)
        return None
    return os.environ[key]


def _fetch_from_ssm(key, assume_role):
    return get_parameter(assume_role, key)


def replace_placeholder(value, tf_outputs, assume_role):
    if type(value) == str:
        pattern = re.compile(r"\${(.+):(.+)}")
        result = pattern.search(value)
        if result is None:
            return value
        elif result.group(1) == "tf":
            value = _fetch_from_tfstate(result.group(2), tf_outputs)
        elif result.group(1) == "ssm":
            value = _fetch_from_ssm(result.group(2), assume_role)
        elif result.group(1) == "env":
            value = _fetch_from_env(result.group(2))
        return value
    elif type(value) == list:
        return [replace_placeholder(i, tf_outputs, assume_role) for i in value]
    elif type(value) == dict:
        return {
            k: replace_placeholder(i, tf_outputs, assume_role) for k, i in value.items()
        }
    return value
