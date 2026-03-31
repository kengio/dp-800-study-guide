---
title: Deployment Pipelines for Database Projects
type: study-material
tags:
  - dp-800
  - deployment
  - schema-drift
  - secrets-management
---

# Deployment Pipelines for Database Projects

## Overview

CI/CD pipelines automate the build, validation, and deployment of SQL Database Projects. Key concerns include detecting schema drift between the source-controlled dacpac and the live database, managing secrets securely with Azure Key Vault, and controlling deployments through approval gates and branch policies.

> [!abstract]
> - Covers CI/CD pipeline setup for database projects: build, test, and deploy stages using GitHub Actions or Azure Pipelines
> - Automated deployment uses SqlPackage.exe with a publish profile for environment-specific settings
> - Key exam topics: SqlPackage.exe action verbs, publish profile (.publish.xml) purpose, pipeline stage order

> [!tip] What the Exam Tests
> - `SqlPackage.exe /Action:Publish` deploys a dacpac to a target; `/Action:Extract` creates dacpac from existing DB; `/Action:Export` creates bacpac
> - **Publish profile** (`.publish.xml`) stores environment-specific connection strings and deployment options — keeps secrets out of pipeline YAML
> - Pipeline order: Build → (optional) Test → Publish to staging → validate → Publish to production

---

---

## Pipeline Architecture

```text
Developer pushes to feature branch
         │
         ▼
┌─────────────────────┐
│  CI Build Pipeline  │  ← triggers on: PR to main
│  - dotnet build     │
│  - Run tSQLt tests  │
│  - Publish dacpac   │
└────────┬────────────┘
         │ artifact: MyDatabase.dacpac
         ▼
┌─────────────────────┐
│  CD Deploy: Dev     │  ← auto-deploy on merge to main
│  - sqlpackage       │
│  - Smoke tests      │
└────────┬────────────┘
         │ approval gate
         ▼
┌─────────────────────┐
│  CD Deploy: Staging │  ← approval required
│  - Drift detection  │
│  - sqlpackage       │
└────────┬────────────┘
         │ approval gate + change window
         ▼
┌─────────────────────┐
│  CD Deploy: Prod    │  ← approval required
│  - sqlpackage       │
└─────────────────────┘
```

---

## CI Pipeline — Build and Test

```yaml
# pipelines/ci.yml (Azure DevOps)
trigger:
  branches:
    include:
      - main
      - feature/*
  paths:
    include:
      - src/MyDatabase/**

pool:
  vmImage: 'ubuntu-latest'

variables:
  buildConfiguration: 'Release'

steps:
  - task: UseDotNet@2
    displayName: 'Install .NET SDK'
    inputs:
      version: '8.x'

  - script: dotnet build src/MyDatabase/MyDatabase.sqlproj --configuration $(buildConfiguration)
    displayName: 'Build SQL Database Project'

  - task: SqlAzureDacpacDeployment@1
    displayName: 'Deploy to Dev for testing'
    inputs:
      azureSubscription: 'MyServiceConnection'
      AuthenticationType: 'servicePrincipal'
      ServerName: '$(DEV_SERVER)'
      DatabaseName: '$(DEV_DATABASE)'
      deployType: 'DacpacTask'
      DeploymentAction: 'Publish'
      DacpacFile: 'src/MyDatabase/bin/Release/MyDatabase.dacpac'
      AdditionalArguments: '/p:BlockOnPossibleDataLoss=true'

  - script: |
      sqlcmd -S $(DEV_SERVER) -d $(DEV_DATABASE) \
        -Q "EXEC tSQLt.RunAll;" \
        --authentication-method ActiveDirectoryDefault
    displayName: 'Run tSQLt unit tests'

  - task: PublishBuildArtifacts@1
    displayName: 'Publish dacpac artifact'
    inputs:
      PathtoPublish: 'src/MyDatabase/bin/Release/MyDatabase.dacpac'
      ArtifactName: 'dacpac'
```

---

## Detecting Schema Drift

**Schema drift** occurs when the live database has been changed outside of the CI/CD pipeline (e.g., emergency hotfix applied directly). Detect it before deployment to avoid surprises.

```yaml
# In the deployment pipeline, before deploying:
  - script: |
      # Extract current database schema to dacpac
      sqlpackage /Action:Extract \
        /TargetFile:$(Agent.TempDirectory)/current.dacpac \
        /SourceConnectionString:"Server=$(TARGET_SERVER);Database=$(TARGET_DB);Authentication=Active Directory Default"

      # Generate a drift report (diff between current DB and source-controlled dacpac)
      sqlpackage /Action:DeployReport \
        /SourceFile:$(Pipeline.Workspace)/dacpac/MyDatabase.dacpac \
        /TargetFile:$(Agent.TempDirectory)/current.dacpac \
        /OutputPath:$(Agent.TempDirectory)/drift-report.xml

      # Fail pipeline if drift report contains unexpected changes
      python3 check-drift.py $(Agent.TempDirectory)/drift-report.xml
    displayName: 'Detect schema drift'
```

```python
# check-drift.py — simple drift checker
import sys
import xml.etree.ElementTree as ET

report_path = sys.argv[1]
tree = ET.parse(report_path)
root = tree.getroot()

operations = root.findall('.//{http://schemas.microsoft.com/sqlserver/dac/DeployReport/2012/02}Operation')

if operations:
    print(f"WARNING: {len(operations)} drift operation(s) detected:")
    for op in operations:
        print(f"  - {op.get('Name')}: {op.text}")
    sys.exit(1)  # Fail the pipeline
else:
    print("No schema drift detected.")
    sys.exit(0)
```

### Manual Drift Check via sqlpackage Script Action

```bash
# Generate the deployment T-SQL script without executing it
# Review this script to understand exactly what will change
sqlpackage /Action:Script \
    /SourceFile:bin/Release/MyDatabase.dacpac \
    /TargetConnectionString:"Server=prod.database.windows.net;Database=MyDB;Authentication=Active Directory Default" \
    /OutputPath:./planned-changes.sql

# Review planned-changes.sql before approving deployment
```

> [!warning] Common Mistake
> SqlPackage action verbs are frequently tested. Publish = deploy dacpac TO a database. Extract = create dacpac FROM a database. Export = create bacpac (schema+data) FROM a database. Import = deploy bacpac TO a database. Mix these up and you'll get wrong answers.

---

## Secrets Management with Azure Key Vault

Connection strings and credentials must never be stored in YAML pipeline files or source code.

### Azure Key Vault Integration in Pipelines

```yaml
# Reference Key Vault secrets in Azure DevOps pipeline
variables:
  - group: 'MyDatabase-KeyVault'  # Variable group linked to Key Vault

# Variable group setup (in Azure DevOps):
# 1. Library → Variable Groups → Link secrets from Azure Key Vault
# 2. Select secrets: sql-connection-string, sql-admin-password
# 3. Reference as $(sql-connection-string) in pipeline steps
```

```yaml
# Alternative: direct Key Vault task
steps:
  - task: AzureKeyVault@2
    displayName: 'Fetch secrets from Key Vault'
    inputs:
      azureSubscription: 'MyServiceConnection'
      KeyVaultName: 'my-keyvault'
      SecretsFilter: 'sql-connection-string,deployment-password'
      RunAsPreJob: true

  - script: |
      sqlpackage /Action:Publish \
        /SourceFile:MyDatabase.dacpac \
        /TargetConnectionString:"$(sql-connection-string)"
    displayName: 'Deploy database'
```

### Service Principal Authentication (Preferred Over Passwords)

```yaml
# Using Managed Identity / Service Principal — no password in pipeline
steps:
  - task: SqlAzureDacpacDeployment@1
    inputs:
      azureSubscription: 'MyServiceConnection'  # Service connection uses SP
      AuthenticationType: 'servicePrincipal'
      ServerName: '$(TARGET_SERVER)'
      DatabaseName: '$(TARGET_DATABASE)'
      deployType: 'DacpacTask'
      DeploymentAction: 'Publish'
      DacpacFile: '$(dacpacPath)'
```

---

## Deployment Pipeline Controls

### Approval Gates

```yaml
# deploy-staging.yml — with approval gate
stages:
  - stage: DeployStaging
    displayName: 'Deploy to Staging'
    dependsOn: BuildAndTest
    condition: and(succeeded(), eq(variables['Build.SourceBranch'], 'refs/heads/main'))
    jobs:
      - deployment: DeployToStaging
        environment: 'Staging'     # ← environment has approval policy configured
        strategy:
          runOnce:
            deploy:
              steps:
                - download: current
                  artifact: dacpac
                - script: |
                    sqlpackage /Action:Publish \
                      /SourceFile:$(Pipeline.Workspace)/dacpac/MyDatabase.dacpac \
                      /TargetConnectionString:"$(staging-connection-string)" \
                      /p:BlockOnPossibleDataLoss=true
                  displayName: 'Deploy to Staging'

  - stage: DeployProduction
    displayName: 'Deploy to Production'
    dependsOn: DeployStaging
    jobs:
      - deployment: DeployToProduction
        environment: 'Production'  # ← requires approval from DBA team
        strategy:
          runOnce:
            deploy:
              steps:
                - download: current
                  artifact: dacpac
                - script: |
                    sqlpackage /Action:Publish \
                      /SourceFile:$(Pipeline.Workspace)/dacpac/MyDatabase.dacpac \
                      /TargetConnectionString:"$(prod-connection-string)" \
                      /p:BlockOnPossibleDataLoss=true \
                      /p:IncludeTransactionalScripts=true
                  displayName: 'Deploy to Production'
```

### Branch Policies as Deployment Gate

```text
Azure DevOps Branch Policies for 'main':
├── Require minimum reviewers: 2
├── Check for linked work items
├── Require successful build (runs CI pipeline)
├── Require approval from CODEOWNERS (@dba-team for Schema/ changes)
└── Require up-to-date before merging (prevents stale PRs)
```

### Environment-Specific sqlpackage Options

```bash
# Development: permissive — allow data loss, drop objects
sqlpackage /Action:Publish \
    /SourceFile:MyDatabase.dacpac \
    /TargetConnectionString:"$(dev-connection-string)" \
    /p:BlockOnPossibleDataLoss=false \
    /p:DropObjectsNotInSource=true

# Staging: moderate — block data loss, don't drop
sqlpackage /Action:Publish \
    /SourceFile:MyDatabase.dacpac \
    /TargetConnectionString:"$(staging-connection-string)" \
    /p:BlockOnPossibleDataLoss=true \
    /p:DropObjectsNotInSource=false

# Production: strict — transactional, block data loss
sqlpackage /Action:Publish \
    /SourceFile:MyDatabase.dacpac \
    /TargetConnectionString:"$(prod-connection-string)" \
    /p:BlockOnPossibleDataLoss=true \
    /p:DropObjectsNotInSource=false \
    /p:IncludeTransactionalScripts=true \
    /p:GenerateSmartDefaults=true
```

---

## Use Cases

- **CI pipeline**: Validates that every PR produces a valid dacpac and passes tests before merging
- **Schema drift detection**: Alerts when production was modified outside of the pipeline — ensures the next deployment won't be a surprise
- **Key Vault integration**: Safely injects connection strings into pipelines without hardcoding credentials
- **Approval gates**: Require DBA sign-off before staging and production deployments

---

## Common Issues & Errors

| Issue | Cause | Fix |
| :--- | :--- | :--- |
| `BlockOnPossibleDataLoss` fails pipeline | Column dropped or type changed | Review change; migrate data in pre-deployment script first |
| Key Vault secret not found | Service principal lacks Get/List permissions | Add SP to Key Vault access policy with `get` and `list` |
| `Environment not configured` | No approval policy on environment | Go to Pipelines → Environments → configure approvals |
| Drift detected on first run | DB was previously managed manually | ==Use `DropObjectsNotInSource=false` on first deployment; then clean up manually== |
| `Authentication failed` in pipeline | Service connection not granted db_owner | Grant the service principal `db_owner` role in the target database |

---

## Exam Tips

> [!tip] Exam Tips
> - **Secrets management**: Connection strings in pipelines should always come from Azure Key Vault or service connections — never hardcoded
> - **Approval environments**: Azure DevOps Environments with approval policies are the mechanism for requiring human sign-off before deployment
> - **`/p:BlockOnPossibleDataLoss=true`** is the critical safety flag for production — fail early rather than lose data
> - **Schema drift** detection uses `sqlpackage /Action:DeployReport` to compare current DB against the dacpac
> - Branch policies (required build, required reviewers) are configured on the branch in Azure DevOps, not in the pipeline YAML

---

## Key Takeaways

- CI pipelines build and test the dacpac; CD pipelines deploy it through environments with approval gates
- Secrets belong in Azure Key Vault — pipelines reference them via variable groups or the AzureKeyVault task
- Drift detection before deployment prevents unexpected changes from causing failures
- `IncludeTransactionalScripts=true` wraps each deployment change in a transaction for safer production rollback

---

## Related Topics

- [02-SQL Database Projects](./02-sql-database-projects.md)
- [03-Source Control & Branching](./03-source-control-branching.md)
- [01-Testing Strategy](./01-testing-strategy.md)

---

## Official Documentation

- [Azure Pipelines with SQL Database Projects](https://learn.microsoft.com/en-us/azure/azure-sql/database/sql-projects-pipelines)
- [sqlpackage Reference](https://learn.microsoft.com/en-us/sql/tools/sqlpackage/sqlpackage)
- [Azure Key Vault in Pipelines](https://learn.microsoft.com/en-us/azure/devops/pipelines/release/azure-key-vault)

---

**[← Previous](./03-source-control-branching.md) | [↑ Back to Section](./cicd-database-projects.md)**
