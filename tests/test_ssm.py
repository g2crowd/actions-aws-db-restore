import pytest
from moto import mock_ssm
from src.ssm import *

ASSUME_ROLE_DISABLED = None


class TestSSM:
    @pytest.fixture
    @mock_ssm
    def conn(self):
        return boto3.client("ssm", region_name="us-east-1")

    @mock_ssm
    def test_get_parameter(self, conn):
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
    def test_get_parameter_which_doesnt_exists(self):
        param_name = "/infra/test/db/username"
        assert get_parameter(ASSUME_ROLE_DISABLED, param_name) == None
