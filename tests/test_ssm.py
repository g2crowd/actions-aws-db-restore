import pytest
from moto import mock_ssm
from src.ssm import *

ASSUME_ROLE_DISABLED = None


@mock_ssm
def init_conn():
    conn = boto3.client("ssm", region_name="us-east-1")
    return conn


@mock_ssm
def test_get_parameter():
    conn = init_conn()
    param_name = "/infra/test/db/username"
    param_value = "test"
    conn.put_parameter(
        Name=param_name,
        Description="A test parameter",
        Value=param_value,
        Type="String",
    )
    assert get_parameter(ASSUME_ROLE_DISABLED, param_name) == param_value


@mock_ssm
def test_get_parameter_which_doesnt_exists():
    param_name = "/infra/test/db/username"
    assert get_parameter(ASSUME_ROLE_DISABLED, param_name) == None
