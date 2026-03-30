---
title: Database Auditing
type: study-material
tags:
  - dp-800
  - auditing
  - sql-audit
  - azure-sql-audit
---

# Database Auditing

## Overview

SQL Server Audit captures database activity events and writes them to a file, Windows Event Log, or Azure Monitor (Log Analytics / Event Hub). Azure SQL has additional managed audit capabilities.

## SQL Server Audit (On-Premises / SQL Managed Instance)

### Creating a Server Audit

```sql
-- Server-level audit (writes to file)
CREATE SERVER AUDIT MyServerAudit
TO FILE (FILEPATH = 'C:\Audit\',
         MAXSIZE = 100 MB,
         MAX_ROLLOVER_FILES = 5,
         RESERVE_DISK_SPACE = OFF)
WITH (QUEUE_DELAY = 1000,        -- ms before writing
      ON_FAILURE = CONTINUE);    -- CONTINUE or SHUTDOWN

ALTER SERVER AUDIT MyServerAudit WITH (STATE = ON);
```

### Database Audit Specification

```sql
-- Audit specific database actions
CREATE DATABASE AUDIT SPECIFICATION MyDBSpec
FOR SERVER AUDIT MyServerAudit
ADD (SELECT ON dbo.Customers BY PUBLIC),
ADD (INSERT, UPDATE, DELETE ON dbo.Orders BY PUBLIC),
ADD (EXECUTE ON dbo.usp_TransferFunds BY PUBLIC),
ADD (SCHEMA_OBJECT_ACCESS_GROUP)   -- all object access
WITH (STATE = ON);
```

### Server Audit Specification

```sql
-- Audit server-level events
CREATE SERVER AUDIT SPECIFICATION MyServerSpec
FOR SERVER AUDIT MyServerAudit
ADD (FAILED_LOGIN_GROUP),
ADD (SUCCESSFUL_LOGIN_GROUP),
ADD (SERVER_PERMISSION_CHANGE_GROUP),
ADD (DATABASE_CHANGE_GROUP)
WITH (STATE = ON);
```

### Reading Audit Logs

```sql
-- Read from audit file
SELECT
    event_time,
    action_id,
    succeeded,
    session_server_principal_name AS LoginName,
    object_name,
    statement
FROM sys.fn_get_audit_file('C:\Audit\MyServerAudit_*.sqlaudit', DEFAULT, DEFAULT)
ORDER BY event_time DESC;
```

## Azure SQL Auditing

Azure SQL Database auditing writes to Azure Blob Storage, Log Analytics, or Event Hub.

### Enabling via Portal

```text
Azure SQL Database → Security → Auditing
→ Toggle "Enable Azure SQL Auditing" ON
→ Choose storage: Storage account / Log Analytics / Event Hub
→ Set retention days (0 = unlimited)
```

### Enabling via T-SQL / PowerShell

```powershell
# Enable auditing to Log Analytics
Set-AzSqlDatabaseAudit `
    -ResourceGroupName "myRG" `
    -ServerName "myserver" `
    -DatabaseName "mydb" `
    -AuditActionGroup "SUCCESSFUL_DATABASE_AUTHENTICATION_GROUP","FAILED_DATABASE_AUTHENTICATION_GROUP","BATCH_COMPLETED_GROUP" `
    -WorkspaceResourceId "/subscriptions/.../workspaces/myworkspace" `
    -LogAnalyticsTargetState Enabled
```

### Common Audit Action Groups

| Action Group | What It Captures |
| :--- | :--- |
| `BATCH_COMPLETED_GROUP` | All T-SQL queries and stored procedures |
| `SUCCESSFUL_DATABASE_AUTHENTICATION_GROUP` | Successful logins |
| `FAILED_DATABASE_AUTHENTICATION_GROUP` | Failed login attempts |
| `DATABASE_PERMISSION_CHANGE_GROUP` | GRANT/DENY/REVOKE statements |
| `SCHEMA_OBJECT_ACCESS_GROUP` | SELECT/INSERT/UPDATE/DELETE on objects |
| `DATABASE_PRINCIPAL_CHANGE_GROUP` | CREATE/DROP users and roles |

### Querying Audit Logs in Log Analytics

```kusto
// KQL query in Log Analytics
AzureDiagnostics
| where Category == "SQLSecurityAuditEvents"
| where database_name_s == "mydb"
| where action_name_s == "SELECT"
| where succeeded_s == "false"
| project TimeGenerated, client_ip_s, server_principal_name_s, statement_s
| order by TimeGenerated desc
```

## Auditing Best Practices

```sql
-- Minimum recommended audit events for compliance:
-- 1. All failed logins
-- 2. DDL changes (CREATE/ALTER/DROP)
-- 3. Permission changes (GRANT/DENY/REVOKE)
-- 4. Access to sensitive tables
-- 5. Execution of privileged procedures
```

## Use Cases

- **Compliance**: GDPR, HIPAA, SOC2 require audit trails for data access
- **Security investigation**: Identify who accessed what data and when
- **Anomaly detection**: Send audit logs to SIEM for alerting on suspicious patterns

## Common Issues & Errors

| Issue | Cause | Resolution |
| :--- | :--- | :--- |
| Audit not capturing queries | Using `SCHEMA_OBJECT_ACCESS_GROUP` but object not in schema | Check the specific object-level audit action |
| Log Analytics latency | Audit events take ~5-10 minutes | This is expected; not real-time |
| Disk full, audit shutdown | `ON_FAILURE = SHUTDOWN` and disk full | Set `ON_FAILURE = CONTINUE` for non-critical; monitor disk |

## Exam Tips

- Azure SQL auditing destination options: **Storage account**, **Log Analytics**, **Event Hub**
- Server-level audit action groups capture broad categories; table-level captures specific objects
- `ON_FAILURE = SHUTDOWN` stops the SQL Server if auditing fails (high security); `CONTINUE` is more forgiving

## Key Takeaways

- SQL Server Audit uses server audit + database/server audit specification
- Azure SQL audit integrates natively with Azure Monitor (Log Analytics and Event Hub)
- Log Analytics uses KQL for querying audit logs; Event Hub for streaming to SIEM

## Related Topics

- [03-Permissions & Access](./03-permissions-access.md)
- [02-Specialized Tables — Ledger](../01-database-objects/02-specialized-tables.md)
- [03-Monitoring](../08-azure-services-integration/03-monitoring.md)

## Official Documentation

- [SQL Server Audit](https://learn.microsoft.com/en-us/sql/relational-databases/security/auditing/sql-server-audit-database-engine)
- [Azure SQL Auditing](https://learn.microsoft.com/en-us/azure/azure-sql/database/auditing-overview)

---

**[← Previous](./03-permissions-access.md) | [↑ Back to Section](./README.md) | [Next →](./05-secure-endpoints.md)**
