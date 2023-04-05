import pytest
from moto import mock_s3
from src.tf import *

ASSUME_ROLE_DISABLED = None


@mock_s3
def init_conn():
    conn = boto3.client("s3", region_name="us-east-1")
    return conn


@mock_s3
def test_get_parameter():
    conn = init_conn()
    state_file = "g2dev-tf-state/staging/terraform.tfstate"
    conn.create_bucket(Bucket="g2dev-tf-state")
    assert get_outputs(ASSUME_ROLE_DISABLED, state_file) == None
