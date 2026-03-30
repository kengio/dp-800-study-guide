---
title: SQL Database Projects (SDK-Style)
type: study-material
tags:
  - dp-800
  - sql-database-projects
  - dacpac
  - sdk-style
---

# SQL Database Projects (SDK-Style)

## Overview

SQL Database Projects allow you to version-control your entire database schema as T-SQL source files and build a deployable dacpac artifact. The modern SDK-style `.sqlproj` format (using `Microsoft.Build.Sql`) integrates with standard `dotnet` tooling and CI/CD pipelines. A dacpac captures the desired state of a database schema — deployment calculates and applies the diff.

## SDK-Style Project Format

The SDK-style project file is minimal compared to the legacy format:

```xml
<!-- MyDatabase.sqlproj -->
<Project Sdk="Microsoft.Build.Sql/0.1.18">
  <PropertyGroup>
    <Name>MyDatabase</Name>
    <DSP>Microsoft.Data.Tools.Schema.Sql.SqlAzureV12DatabaseSchemaProvider</DSP>
    <ModelCollation>1033, CI</ModelCollation>
  </PropertyGroup>
</Project>
```

Key differences from the legacy format:
- All `.sql` files in the project directory are **automatically included** (no explicit `<Build Include="..."/>` entries needed)
- Uses standard MSBuild SDK conventions
- Compatible with `dotnet build` CLI
- Supports NuGet package references for shared objects

## Project Directory Structure

```text
MyDatabase/
├── MyDatabase.sqlproj          ← project file
├── Schema/
│   ├── Tables/
│   │   ├── dbo.Customers.sql
│   │   ├── dbo.Orders.sql
│   │   └── dbo.OrderItems.sql
│   ├── Views/
│   │   └── dbo.vw_ActiveOrders.sql
│   ├── StoredProcedures/
│   │   ├── dbo.CreateOrder.sql
│   │   └── dbo.GetOrderSummary.sql
│   ├── Functions/
│   │   └── dbo.CalculateOrderTotal.sql
│   └── Indexes/
│       └── dbo.Orders.IX_CustomerId.sql
├── Security/
│   └── Roles/
│       └── dbo.OrdersReader.sql
├── Scripts/
│   ├── PreDeployment/
│   │   └── PreDeployment.sql   ← runs before schema changes
│   └── PostDeployment/
│       └── PostDeployment.sql  ← runs after schema changes
└── Tests/
    └── OrderTests/
        └── test_CreateOrder.sql
```

## SQL Object Definitions

Each object is defined in its own `.sql` file using `CREATE OR ALTER` (preferred) or plain `CREATE`:

```sql
-- Schema/Tables/dbo.Orders.sql
CREATE TABLE [dbo].[Orders]
(
    [OrderId]    INT           NOT NULL IDENTITY(1,1),
    [CustomerId] INT           NOT NULL,
    [OrderDate]  DATETIME2     NOT NULL DEFAULT GETUTCDATE(),
    [Status]     NVARCHAR(20)  NOT NULL DEFAULT 'Pending',
    [TotalAmount] DECIMAL(10,2) NOT NULL DEFAULT 0,
    CONSTRAINT [PK_Orders] PRIMARY KEY CLUSTERED ([OrderId] ASC),
    CONSTRAINT [FK_Orders_Customers]
        FOREIGN KEY ([CustomerId]) REFERENCES [dbo].[Customers] ([CustomerId])
);
```

```sql
-- Schema/StoredProcedures/dbo.CreateOrder.sql
CREATE OR ALTER PROCEDURE [dbo].[CreateOrder]
    @CustomerId INT,
    @ProductId  INT,
    @Quantity   INT,
    @OrderId    INT OUTPUT
AS
BEGIN
    SET NOCOUNT ON;

    INSERT INTO dbo.Orders (CustomerId, Status)
    VALUES (@CustomerId, 'Pending');

    SET @OrderId = SCOPE_IDENTITY();

    INSERT INTO dbo.OrderItems (OrderId, ProductId, Quantity)
    VALUES (@OrderId, @ProductId, @Quantity);
END;
```

## Pre- and Post-Deployment Scripts

Pre- and post-deployment scripts run **outside** the dacpac schema comparison — they always execute in order.

```sql
-- Scripts/PreDeployment/PreDeployment.sql
-- Runs BEFORE schema changes — use for data migrations that must happen first

PRINT 'Pre-deployment: backing up critical data...';

-- Example: move data before dropping a column
IF EXISTS (SELECT 1 FROM sys.columns
           WHERE object_id = OBJECT_ID('dbo.Orders')
           AND name = 'LegacyCode')
BEGIN
    UPDATE dbo.Orders
    SET Notes = CONCAT(Notes, ' [Legacy: ', LegacyCode, ']')
    WHERE LegacyCode IS NOT NULL;
END;
```

```sql
-- Scripts/PostDeployment/PostDeployment.sql
-- Runs AFTER schema changes — use for reference data and final configuration

PRINT 'Post-deployment: loading reference data...';

:r .\..\..\Data\ReferenceData\dbo.OrderStatus.data.sql
:r .\..\..\Data\ReferenceData\dbo.Countries.data.sql

PRINT 'Post-deployment complete.';
```

To mark a script as pre/post-deployment, set the Build Action in the project:

```xml
<!-- MyDatabase.sqlproj — explicit script references -->
<ItemGroup>
  <PreDeploy Include="Scripts\PreDeployment\PreDeployment.sql" />
  <PostDeploy Include="Scripts\PostDeployment\PostDeployment.sql" />
  <!-- Exclude test files from dacpac build -->
  <None Include="Tests\**\*.sql" />
</ItemGroup>
```

## Building with dotnet

```bash
# Install the SQL Database Projects SDK (if not already installed)
dotnet tool install -g microsoft.sqlpackage

# Build the project — produces a .dacpac artifact
dotnet build MyDatabase.sqlproj

# Output:
# bin/Debug/MyDatabase.dacpac

# Build in Release configuration (for CI/CD)
dotnet build MyDatabase.sqlproj --configuration Release
# Output:
# bin/Release/MyDatabase.dacpac
```

## Validating and Deploying with sqlpackage

```bash
# Validate (what changes would be applied — no deployment)
sqlpackage /Action:Script \
    /SourceFile:bin/Release/MyDatabase.dacpac \
    /TargetConnectionString:"Server=myserver.database.windows.net;Database=MyDB;Authentication=Active Directory Default" \
    /OutputPath:./deployment-script.sql

# Deploy to target database
sqlpackage /Action:Publish \
    /SourceFile:bin/Release/MyDatabase.dacpac \
    /TargetConnectionString:"Server=myserver.database.windows.net;Database=MyDB;Authentication=Active Directory Default"

# Deploy with specific options
sqlpackage /Action:Publish \
    /SourceFile:bin/Release/MyDatabase.dacpac \
    /TargetConnectionString:"..." \
    /p:BlockOnPossibleDataLoss=true \
    /p:DropObjectsNotInSource=false \
    /p:GenerateSmartDefaults=true

# Compare two dacpacs (useful for drift detection)
sqlpackage /Action:DeployReport \
    /SourceFile:bin/Release/MyDatabase.dacpac \
    /TargetFile:current-schema.dacpac \
    /OutputPath:./drift-report.xml
```

### Key sqlpackage Properties

| Property | Default | Description |
| :--- | :--- | :--- |
| `BlockOnPossibleDataLoss` | `true` | Fail if deployment might lose data (column drops, type changes) |
| `DropObjectsNotInSource` | `false` | Drop DB objects not in the dacpac (use with caution) |
| `GenerateSmartDefaults` | `false` | Auto-generate default values when adding NOT NULL columns |
| `IncludeTransactionalScripts` | `false` | Wrap each change in a transaction for safer rollback |

## Extracting an Existing Database to dacpac

```bash
# Extract current database schema into a dacpac
sqlpackage /Action:Extract \
    /TargetFile:./current-schema.dacpac \
    /SourceConnectionString:"Server=myserver.database.windows.net;Database=MyDB;Authentication=Active Directory Default"

# Export schema + data (bacpac format)
sqlpackage /Action:Export \
    /TargetFile:./database-backup.bacpac \
    /SourceConnectionString:"..."
```

## NuGet Package References

SDK-style projects support referencing shared objects as NuGet packages:

```xml
<!-- Reference shared objects (e.g., shared security schema) from NuGet -->
<ItemGroup>
  <PackageReference Include="MyCompany.SharedSecurity.Dacpac" Version="1.0.0" />
</ItemGroup>
```

## Use Cases

- **Schema-as-code**: Every table, view, and stored procedure is a `.sql` file in source control — enables code review, diff tracking, and branching
- **dacpac deployment**: Deploy only the changes needed to bring target database to desired state — no manual delta scripts
- **CI/CD pipelines**: `dotnet build` produces the artifact; `sqlpackage publish` deploys it
- **Drift detection**: Extract current DB to dacpac and diff against source-controlled dacpac

## Common Issues & Errors

| Issue | Cause | Fix |
| :--- | :--- | :--- |
| `Unresolved reference to object` | Object referenced before it's defined | Use fully qualified names; SQL projects resolve by dependency order |
| `BlockOnPossibleDataLoss` error | Column drop or type change detected | Review the change; use pre-deployment script to migrate data first |
| Pre/post scripts not running | Build Action not set correctly | Add `<PreDeploy>` / `<PostDeploy>` elements in `.sqlproj` |
| Test files included in dacpac | No exclusion rule | Add `<None Include="Tests\**\*.sql" />` to project |
| `DSP` property mismatch | Wrong schema provider for target | Set DSP to match target: `SqlAzureV12` for Azure SQL |

## Exam Tips

- SDK-style projects use `<Project Sdk="Microsoft.Build.Sql/...">` — all `.sql` files are automatically included
- The dacpac represents the **desired state** — deployment is always a diff, never a full recreate
- `BlockOnPossibleDataLoss=true` is the safety net for production deployments — it prevents accidental data loss
- Pre-deployment scripts handle data migrations that must happen before schema changes (e.g., moving data before dropping a column)
- Post-deployment scripts handle reference data loads and are always run after the dacpac schema changes complete

## Key Takeaways

- SDK-style `.sqlproj` builds with `dotnet build` and deploys with `sqlpackage` — standard CI/CD tooling
- One SQL object per file is the convention — makes diffs readable in pull requests
- dacpac deployment is idempotent and state-based — safe to run multiple times
- Pre/post scripts run outside the dacpac diff and always execute in order

## Related Topics

- [01-Testing Strategy](./01-testing-strategy.md)
- [03-Source Control & Branching](./03-source-control-branching.md)
- [04-Deployment Pipelines](./04-deployment-pipelines.md)

## Official Documentation

- [SQL Database Projects Overview](https://learn.microsoft.com/en-us/azure/azure-sql/database/sql-projects-overview)
- [sqlpackage CLI Reference](https://learn.microsoft.com/en-us/sql/tools/sqlpackage/sqlpackage)
- [SDK-style SQL Projects](https://learn.microsoft.com/en-us/sql/tools/sql-database-projects/concepts/sdk-style-projects)

---

**[← Previous](./01-testing-strategy.md) | [↑ Back to Section](./README.md) | [Next →](./03-source-control-branching.md)**
