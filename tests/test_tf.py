import pytest
from moto import mock_s3
from src.tf import *

ASSUME_ROLE_DISABLED = None


class TestTF:
    @pytest.fixture
    @mock_s3
    def conn(self):
        return boto3.client("s3", region_name="us-east-1")

    @mock_s3
    def test_get_output_where_state_file_doesnt_exists(self, conn):
        state_file = "g2dev-tf-state/staging/terraform.tfstate"
        conn.create_bucket(Bucket="g2dev-tf-state")
        assert get_outputs(ASSUME_ROLE_DISABLED, state_file) == None
