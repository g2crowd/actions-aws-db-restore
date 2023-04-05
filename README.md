# Restore RDS snapshot GitHub Action

This is a GitHub action to restore RDS DB snapshot.

[![GitHub Super-Linter](https://github.com/g2crowd/action-aws-db-restore/workflows/Lint%20Code%20Base/badge.svg)](https://github.com/marketplace/actions/super-linter)

## Table of Contents

<!-- toc -->

* [Usage](#usage)
* [Inputs](#inputs)
* [Permissions](#permissions)

<!-- tocstop -->

## Usage
```yaml
    - name: Restore DB snapshot from another account
      uses: g2crowd/aaction-aws-db-restore@main
      with:
        config: .config/sample.json
        tfstate: g2dev-tf-state/staging/terraform.tfstate
```

## Inputs

* config (**Required**): The configuration file path
* tfstate : The TF state file path


## Configuration File
Config file can have values which are stored in
* Environment variable: *${env:<env_variable_name>}*
* Terraform state: *${tf:<output_variable_name>}*
* SSM parameter store: *${ssm:<ssm_parameter_name>}*

Sample config file -
```json
{
  "ClusterMode":false,
  "DeleteExistingTarget":true,
  "Source":{
    "Share":{
      "AssumeRole":"arn:aws:iam::345678901:role/db_restore_share_role",
      "TargetAccount":"123456789",
      "SourceKmsKey":"alias/db_restore",
      "TargetKmsKey":"alias/aws/rds"
    },
    "DBIdentifier":"dash-staging"
  },
  "Target":{
    "AssumeRole":"arn:aws:iam::123456789:role/db_restore_role",
    "DBIdentifier":"dash-staging",
    "VpcSecurityGroupIds":"${tf:db_global_security_group}",
    "DBSubnetGroupName":"${tf:db_staging_private_subnet}",
    "DBInstanceClass":"db.t3.medium",
    "PubliclyAccessible":false,
    "Tags":[
      {
        "Key":"dbrestore",
        "Value":"enable"
      }
    ]
  }
}
```

## Permissions

This action requires the following minimum set of permissions:

Restore Role Policy (in target) -
```json
{
    "Version" : "2012-10-17",
    "Statement" : [
      {
        "Sid" : "SnapshotRestoreAccess",
        "Action" : [
          "rds:DescribeDBInstances",
          "rds:DescribeDBClusters",
          "rds:CreateDBInstance",
          "rds:CreateDBCluster",
          "rds:DescribeDBSnapshots",
          "rds:DescribeDBClusterSnapshots",
          "rds:RestoreDBInstanceFromDBSnapshot",
          "rds:RestoreDBClusterFromSnapshot",
          "rds:CopyDBClusterSnapshot",
          "rds:CopyDBSnapshot",
          "rds:AddTagsToResource"
        ],
        "Effect" : "Allow",
        "Resource" : [
          "*"
        ]
      },
      {
        "Sid" : "SnapshotRestoreWriteAccess",
        "Action" : [
          "rds:DeleteDBInstance",
          "rds:DeleteDBCluster",
          "rds:ModifyDBInstance",
          "rds:ModifyDBCluster"
        ],
        "Effect" : "Allow",
        "Resource" : [
          "*"
        ],
        "Condition" : {
          "ForAllValues:StringEquals" : {
            "rds:db-tag/dbrestore" : [
              "enable"
            ]
          }
        }
      },
      {
        "Sid" : "AllowUseOfTheKey",
        "Effect" : "Allow",
        "Action" : [
          "kms:Encrypt",
          "kms:Decrypt",
          "kms:ReEncrypt*",
          "kms:GenerateDataKey*",
          "kms:DescribeKey"
        ],
        "Resource" : "${aws_kms_key.db_restore.arn}"
      },
      {
        "Sid" : "AllowAttachmentOfPersistentResources",
        "Effect" : "Allow",
        "Action" : [
          "kms:CreateGrant",
          "kms:ListGrants",
          "kms:RevokeGrant"
        ],
        "Resource" : "${aws_kms_key.db_restore.arn}",
        "Condition" : {
          "Bool" : {
            "kms:GrantIsForAWSResource" : true
          }
        }
      },
      {
        "Sid" : "AllowReencryptionOfNewCMK",
        "Effect" : "Allow",
        "Action" : [
          "kms:ReEncryptTo*",
          "kms:ReEncryptFrom*"
        ],
        "Resource" : "*"
      },
      {
        "Sid" : "TFStateReadOnly",
        "Effect" : "Allow",
        "Action" : [
          "s3:GetObject",
          "s3:GetObjectVersion"
        ],
        "Resource" : "arn:aws:s3:::g2dev-tf-state/*"
      }
    ]
  }
```


Share Role Policy (in source, in case of cross account snapshot restore) -
```json
{
  "Version":"2012-10-17",
  "Statement":[
    {
      "Sid":"SnapshotRestoreAccess",
      "Action":[
        "rds:DescribeDBInstances",
        "rds:DescribeDBClusters",
        "rds:DescribeDBSnapshots",
        "rds:DescribeDBClusterSnapshots"
      ],
      "Effect":"Allow",
      "Resource":[
        "*"
      ]
    },
    {
      "Sid":"SnapshotShareAccess",
      "Action":[
        "rds:CopyDBClusterSnapshot",
        "rds:CopyDBSnapshot",
        "rds:ModifyDBClusterSnapshotAttribute",
        "rds:ModifyDBSnapshotAttribute"
      ],
      "Effect":"Allow",
      "Resource":[
        "*"
      ]
    },
    {
      "Effect":"Allow",
      "Action":[
        "kms:CreateGrant",
        "kms:ListGrants",
        "kms:RevokeGrant",
        "kms:DescribeKey"
      ],
      "Resource":"${aws_kms_key.db_restore.arn}"
    }
  ]
}
```

KMS Key Policy (in source, in case of cross account snapshot restore) -
```json
{
  "Version":"2012-10-17",
  "Statement":[
    {
      "Sid":"Enable IAM User Permissions",
      "Effect":"Allow",
      "Principal":{
        "AWS":"arn:aws:iam::${var.aws_account_id}:root"
      },
      "Action":"kms:*",
      "Resource":"*"
    },
    {
      "Sid":"Allow use of the key",
      "Effect":"Allow",
      "Principal":{
        "AWS":[
          "arn:aws:iam::${var.restore_account_id}:root"
        ]
      },
      "Action":[
        "kms:Encrypt",
        "kms:Decrypt",
        "kms:ReEncrypt*",
        "kms:GenerateDataKey*",
        "kms:DescribeKey"
      ],
      "Resource":"*"
    },
    {
      "Sid":"Allow attachment of persistent resources",
      "Effect":"Allow",
      "Principal":{
        "AWS":[
          "arn:aws:iam::${var.restore_account_id}:root"
        ]
      },
      "Action":[
        "kms:CreateGrant",
        "kms:ListGrants",
        "kms:RevokeGrant"
      ],
      "Resource":"*",
      "Condition":{
        "Bool":{
          "kms:GrantIsForAWSResource":"true"
        }
      }
    }
  ]
}
```
