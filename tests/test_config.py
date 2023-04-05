import pytest
from src.config import *


def test_is_config_exists():
    assert is_config_exists("schema/config.json") == True
    assert is_config_exists("schema/conf.json") == False


def test_is_valid():
    data = {
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
            "DBSubnetGroupName": "${tf:db_staging_private_subnet}",
            "CopyTagsToSnapshot": True,
            "DBInstanceClass": "db.t3.medium",
            "PubliclyAccessible": False,
            "Tags": [{"Key": "owner", "Value": "snapshot_restore"}],
        },
    }

    status = is_valid(data)
    assert status == True


def test_is_valid_missing_required_properties():
    data = {
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
            "VpcSecurityGroupIds": "${tf:db_global_security_group}",
            "DBSubnetGroupName": "${tf:db_staging_private_subnet}",
            "CopyTagsToSnapshot": True,
            "DBInstanceClass": "db.t3.medium",
            "PubliclyAccessible": False,
            "Tags": [{"Key": "owner", "Value": "snapshot_restore"}],
        },
    }

    status = is_valid(data)
    assert status == False


def test_is_valid_share_missing():
    data = {
        "ClusterMode": False,
        "DeleteExistingTarget": True,
        "Source": {"DBIdentifier": "dash-staging"},
        "Target": {
            "AssumeRole": "arn:aws:iam::11223334544:role/db_restore_role",
            "DBIdentifier": "dash-staging",
            "VpcSecurityGroupIds": "${tf:db_global_security_group}",
            "DBSubnetGroupName": "${tf:db_staging_private_subnet}",
            "CopyTagsToSnapshot": True,
            "DBInstanceClass": "db.t3.medium",
            "PubliclyAccessible": False,
            "Tags": [{"Key": "owner", "Value": "snapshot_restore"}],
        },
    }

    status = is_valid(data)
    assert status == True
