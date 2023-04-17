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
        conn.create_bucket(Bucket="g2dev-tf-state")
        assert (
            get_outputs(
                ASSUME_ROLE_DISABLED, "g2dev-tf-state/staging/terraform.tfstate"
            )
            is None
        )

    @mock_s3
    def test_get_output_where_state_file_exists(self, conn):
        conn.create_bucket(Bucket="g2dev-tf-state")
        conn.put_object(
            Bucket="g2dev-tf-state",
            Key="staging/terraform.tfstate",
            Body=b'{"outputs":{"db_staging_private_subnet":{"value":"staging-global-private","type":"string"}}}',
        )
        output = get_outputs(
            ASSUME_ROLE_DISABLED, "g2dev-tf-state/staging/terraform.tfstate"
        )
        assert output["db_staging_private_subnet"] == "staging-global-private"
