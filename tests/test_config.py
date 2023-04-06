import os

import pytest
from src.config import *

ASSUME_ROLE_DISABLED = None


class TestConfig:
    def test_is_config_exists_when_file_present(self):
        assert is_config_exists("schema/config.json") == True

    def test_is_config_exists_when_file_not_present(self):
        assert is_config_exists("schema/conf.json") == False

    def test_load_config_exists_when_file_present(self):
        assert load_config("schema/config.json") != None

    def test_load_config_exists_when_file_not_present(self):
        assert load_config("schema/conf.json") == None

    @pytest.fixture
    def data(self):
        return {
            "ClusterMode": False,
            "DeleteExistingTarget": True,
            "Source": {
                "Share": {
                    "AssumeRole": "arn:aws:iam::3211251512:role/db_restore_share_role",
                    "TargetAccount": "11223334544",
                    "SourceKmsKey": "alias/db_restore",
                    "TargetKmsKey": "alias/aws/rds",
                },
                "DBIdentifier": "dash-staging",
            },
            "Target": {
                "AssumeRole": "arn:aws:iam::11223334544:role/db_restore_role",
                "DBIdentifier": "dash-staging",
                "VpcSecurityGroupIds": "${tf:db_global_security_group}",
                "DBSubnetGroupName": "${env:PRIVATE_SUBNET}",
                "CopyTagsToSnapshot": True,
                "DBInstanceClass": "${tf:instance_class}",
                "PubliclyAccessible": False,
                "Tags": [{"Key": "owner", "Value": "snapshot_restore"}],
            },
        }

    @pytest.fixture
    def tfdate(self):
        return {
            "db_global_security_group": ["sg-076cd3b3c6"],
            "db_staging_private_subnet": "staging-global-private",
            "db_staging_public_subnet": "staging-global-public",
            "private_subnets": ["subnet-0127daddc0c", "subnet-0a950bee5c"],
            "public_subnets": ["subnet-0edbc1b60d0", "subnet-621ed974ea"],
        }

    def test_is_valid(self, data):
        assert is_invalid(data) == False

    def test_is_valid_missing_required_property_cluster_mode(self, data):
        invalid_data = data.copy()
        del invalid_data["Target"]["Tags"]
        assert is_invalid(invalid_data) != None

    def test_is_valid_missing_required_property_tags(self, data):
        invalid_data = data.copy().pop("ClusterMode")
        assert is_invalid(invalid_data) != None

    def test_is_valid_missing_optional_property_share(self, data):
        valid_data = data.copy()
        del valid_data["Source"]["Share"]
        assert is_invalid(data) == False

    def test_is_sharing_enabled_with_sharing_property(self, data):
        assert is_sharing_enabled(data["Source"]) != None

    def test_is_sharing_enabled_without_sharing_property(self, data):
        valid_data = data.copy()
        del valid_data["Source"]["Share"]
        assert is_sharing_enabled(valid_data) == False

    def test_fetch_from_tfstate_key_exists(self, tfdate):
        key = "db_global_security_group"
        assert fetch_from_tfstate(key, tfdate) == tfdate.get(key)

    def test_fetch_from_tfstate_key_doesnt_exists(self, tfdate):
        key = "security_group"
        assert fetch_from_tfstate(key, tfdate) == None

    def test_fetch_from_env_key_exists(self, tfdate):
        key = "DB_USERNAME"
        value = "random123"
        os.environ[key] = value
        assert fetch_from_env(key) == value

    def test_fetch_from_env_key_doesnt_exists(self, tfdate):
        key = "MASTER_DB_USERNAME"
        value = "random123"
        assert fetch_from_env(key) == None

    def test_replace_placeholder_env_not_present(self, data, tfdate):
        parsed_data = replace_placeholder(data, tfdate, ASSUME_ROLE_DISABLED)
        assert parsed_data["Target"]["DBSubnetGroupName"] == None

    def test_replace_placeholder_env_present(self, data, tfdate):
        key = "PRIVATE_SUBNET"
        value = "staging-global-private"
        os.environ[key] = value
        parsed_data = replace_placeholder(data, tfdate, ASSUME_ROLE_DISABLED)
        assert parsed_data["Target"]["DBSubnetGroupName"] == value

    def test_replace_placeholder_tfdata_not_present(self, data, tfdate):
        parsed_data = replace_placeholder(data, tfdate, ASSUME_ROLE_DISABLED)
        assert parsed_data["Target"]["DBInstanceClass"] == None

    def test_replace_placeholder_tfdata_present(self, data, tfdate):
        parsed_data = replace_placeholder(data, tfdate, ASSUME_ROLE_DISABLED)
        assert parsed_data["Target"]["VpcSecurityGroupIds"] == ["sg-076cd3b3c6"]
