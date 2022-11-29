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
        config: my-config
```

## Inputs

* config (**Required**): The configuration file path

## Permissions

This action requires the following minimum set of permissions:

```json
{
  "Version":"2012-10-17",
  "Statement":[
    {
      "Sid":"SnapshotRestoreAccess",
      "Action":[
        "rds:DescribeDBInstances",
        "rds:DescribeDBClusters",
        "rds:CreateDBInstance",
        "rds:CreateDBCluster",
        "rds:DescribeDBSnapshots",
        "rds:DescribeDBClusterSnapshots",
        "rds:RestoreDBInstanceFromDBSnapshot",
        "rds:RestoreDBClusterFromSnapshot	"
      ],
      "Effect":"Allow",
      "Resource":[
        "*"
      ]
    },
    {
      "Sid":"SnapshotRestoreWriteAccess",
      "Action":[
        "rds:DeleteDBInstance",
        "rds:DeleteDBCluster",
        "rds:ModifyDBInstance",
        "rds:ModifyDBCluster"
      ],
      "Effect":"Allow",
      "Resource":[
        "*"
      ],
      "Condition":{
        "ForAllValues:StringEquals":{
          "rds:db-tag/AllowWrites":[
            "True"
          ]
        }
      }
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
      ],
      "Condition":{
        "ForAllValues:StringEquals":{
          "rds:db-tag/AllowWrites":[
            "True"
          ]
        }
      }
    }
  ]
}
```
