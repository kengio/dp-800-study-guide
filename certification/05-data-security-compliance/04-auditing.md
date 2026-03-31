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

> [!abstract]
> - Covers SQL Server Audit at the server and database level, audit action groups, and audit log destinations
> - Auditing captures who did what and when — essential for compliance requirements
> - Key exam topics: server-level vs database-level audit, audit destinations, querying audit logs

> [!tip] What the Exam Tests
> - Audit hierarchy: create `SERVER AUDIT` (defines destination) → create `DATABASE AUDIT SPECIFICATION` (defines what to capture)
> - Audit destinations: **Storage Account** (blob), **Log Analytics** workspace, **Event Hub** — all three are valid
> - Query audit logs with `sys.fn_get_audit_file()` for storage-based logs, or via Log Analytics KQL queries

---

## SQL Server Audit Architecture

**SQL Server Audit** is built from two components:

- **Server Audit** — defines WHERE to write audit records (file, Application Event Log, Security Event Log)
- **Audit Specification** — defines WHAT to capture; two types:
  - **Server Audit Specification**: server-scoped actions (logins, server role changes, DDL at server level)
  - **Database Audit Specification**: database-scoped actions (DML, SELECT, schema changes, permission grants)

### Audit Queue Behavior

| Mode | Behavior When Queue Full |
| :--- | :--- |
| Synchronous (`QUEUE_DELAY = 0`) | ==Blocks the session until the event is written== |
| Asynchronous (`QUEUE_DELAY > 0`) | Drops events if the queue fills; `ON_FAILURE` controls what happens |

`ON_FAILURE = CONTINUE` — allows the operation to proceed even if auditing fails (less secure, more available).
`ON_FAILURE = SHUTDOWN` — stops the SQL Server instance if auditing fails (high security, high risk of downtime).

```sql
-- Create server audit writing to file
CREATE SERVER AUDIT DataAudit
TO FILE (FILEPATH = 'C:\AuditLogs\', MAXSIZE = 100 MB)
WITH (QUEUE_DELAY = 1000, ON_FAILURE = CONTINUE);

ALTER SERVER AUDIT DataAudit WITH (STATE = ON);

-- Database audit specification
CREATE DATABASE AUDIT SPECIFICATION DataAuditSpec
FOR SERVER AUDIT DataAudit
ADD (SELECT, INSERT, UPDATE, DELETE ON SCHEMA::dbo BY PUBLIC),
ADD (EXECUTE ON SCHEMA::dbo BY PUBLIC)
WITH (STATE = ON);
```

---

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

---

## Azure SQL Database Auditing

Azure SQL auditing differs from on-premises in key ways:

- No file path — writes to **Azure Blob Storage**, **Log Analytics**, or **Event Hub**
- Enabled via Azure Portal, T-SQL policy, or PowerShell (`Set-AzSqlDatabaseAudit`)
- Retention period configurable in days (0 = unlimited retention)
- Integrates with **Microsoft Defender for SQL** for threat detection and anomaly alerts
- Server-level auditing in Azure SQL applies to all databases on the logical server

### Enabling via Portal

```text
Azure SQL Database → Security → Auditing
→ Toggle "Enable Azure SQL Auditing" ON
→ Choose storage: Storage account / Log Analytics / Event Hub
→ Set retention days (0 = unlimited)
```

### Enabling via T-SQL / PowerShell

```sql
-- Enable Azure SQL auditing to storage account
-- (typically done via portal or PowerShell; T-SQL alternative:)
ALTER DATABASE [MyDatabase]
SET AUDIT_MODE = POLICY;

-- View recent audit records (when using Log Analytics)
-- AzureDiagnostics | where Category == "SQLSecurityAuditEvents"
```

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

---

## Key Audit Action Groups

Important audit action groups for the DP-800 exam:

| Action Group | What It Captures |
| :--- | :--- |
| `BATCH_COMPLETED_GROUP` | ==All T-SQL batches completed (incl. SELECT with full SQL text)== |
| `DATABASE_OBJECT_ACCESS_GROUP` | Access to database objects |
| `DATABASE_OBJECT_PERMISSION_CHANGE_GROUP` | Permission changes on objects |
| `DATABASE_ROLE_MEMBER_CHANGE_GROUP` | Role membership changes |
| `FAILED_DATABASE_AUTHENTICATION_GROUP` | Failed logins to a database |
| `SCHEMA_OBJECT_ACCESS_GROUP` | Table/view/proc accesses |
| `USER_DEFINED_AUDIT_GROUP` | Manual audit events via `sp_audit_write` |

Also commonly used:

| Action Group | What It Captures |
| :--- | :--- |
| `BATCH_COMPLETED_GROUP` | All T-SQL queries and stored procedures |
| `SUCCESSFUL_DATABASE_AUTHENTICATION_GROUP` | Successful logins |
| `DATABASE_PERMISSION_CHANGE_GROUP` | GRANT/DENY/REVOKE statements |
| `DATABASE_PRINCIPAL_CHANGE_GROUP` | CREATE/DROP users and roles |

---

## Querying Audit Logs

Use `sys.fn_get_audit_file` to read on-premises audit files. Key columns returned:

| Column | Description |
| :--- | :--- |
| `event_time` | When the event occurred |
| `action_id` | Short code (SL = SELECT, IN = INSERT, UP = UPDATE, DL = DELETE) |
| `server_principal_name` | Login that performed the action |
| `database_name` | Database where the action occurred |
| `object_name` | Table, view, or procedure accessed |
| `statement` | ==Full SQL text of the batch== |

```sql
-- Read audit log files
SELECT event_time, action_id, server_principal_name,
       database_name, object_name, statement
FROM sys.fn_get_audit_file('C:\AuditLogs\*.sqlaudit', DEFAULT, DEFAULT)
WHERE object_name = 'Salaries'
ORDER BY event_time DESC;

-- Find all data access by a specific user
SELECT event_time, action_id, object_name, statement
FROM sys.fn_get_audit_file('C:\AuditLogs\*.sqlaudit', DEFAULT, DEFAULT)
WHERE server_principal_name = 'DOMAIN\suspicious_user'
AND action_id IN ('SL', 'IN', 'UP', 'DL')  -- SELECT, INSERT, UPDATE, DELETE
ORDER BY event_time;
```

> [!warning] Common Mistake
> Audit logs are NOT queryable from regular DMVs like `sys.dm_exec_sessions` or `sys.dm_audit_actions`. Use `sys.fn_get_audit_file('path\*.sqlaudit', DEFAULT, DEFAULT)` for storage-based logs. The exam may offer DMV queries as distractors.

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

---

## Temporal Tables as Audit Trails

Temporal tables (system-versioned) automatically capture all row changes with timestamps in a history table.

Key differences from SQL Audit:

- Temporal tables track **DATA changes** (INSERT, UPDATE, DELETE) — not SELECT or access events
- They record **what the data was**, not who accessed it (no login/user context in the history table)
- Use `FOR SYSTEM_TIME ALL` to query the full change history of a row
- Useful for **compliance proof** of what a record looked like at any point in time
- **Not a replacement** for SQL Audit — use both together: audit for access/accountability, temporal tables for data lineage

```sql
-- Query full history of a row using temporal syntax
SELECT EmployeeID, Salary, ValidFrom, ValidTo
FROM dbo.Employees
FOR SYSTEM_TIME ALL
WHERE EmployeeID = 42
ORDER BY ValidFrom;
```

---

## Auditing Best Practices

```sql
-- Minimum recommended audit events for compliance:
-- 1. All failed logins
-- 2. DDL changes (CREATE/ALTER/DROP)
-- 3. Permission changes (GRANT/DENY/REVOKE)
-- 4. Access to sensitive tables
-- 5. Execution of privileged procedures
```

---

## Use Cases

- **Compliance**: GDPR, HIPAA, SOC2 require audit trails for data access
- **Security investigation**: Identify who accessed what data and when
- **Anomaly detection**: Send audit logs to SIEM for alerting on suspicious patterns

---

## Common Issues & Errors

| Issue | Cause | Resolution |
| :--- | :--- | :--- |
| Audit not capturing queries | Using `SCHEMA_OBJECT_ACCESS_GROUP` but object not in schema | Check the specific object-level audit action |
| Log Analytics latency | Audit events take ~5-10 minutes | This is expected; not real-time |
| Disk full, audit shutdown | `ON_FAILURE = SHUTDOWN` and disk full | Set `ON_FAILURE = CONTINUE` for non-critical; monitor disk |

---

## Best Practices

- Enable `BATCH_COMPLETED_GROUP` when you need full SQL text captured in audit logs — object-access groups alone do not always record the statement
- Use `ON_FAILURE = CONTINUE` for availability-critical systems; use `SHUTDOWN` only where audit integrity is non-negotiable (e.g., PCI-DSS environments)
- Set a meaningful audit retention period — 0 (unlimited) is fine for Log Analytics but incurs storage costs; align with regulatory requirements
- Combine SQL Audit (who accessed what) with temporal tables (what the data was) for a complete compliance story
- For Azure SQL, prefer server-level auditing over database-level to ensure all databases are covered, including future ones

---

## Exam Tips

- Azure SQL auditing destination options: **Storage account**, **Log Analytics**, **Event Hub**
- Server-level audit action groups capture broad categories; table-level captures specific objects
- `ON_FAILURE = SHUTDOWN` stops the SQL Server if auditing fails (high security); `CONTINUE` is more forgiving
- `BATCH_COMPLETED_GROUP` is the only action group that captures full SQL statement text — key for SELECT auditing
- Temporal tables capture data history (WHAT changed) but NOT access events (WHO accessed); SQL Audit captures access

---

## Key Takeaways

- SQL Server Audit uses server audit + database/server audit specification
- Azure SQL audit integrates natively with Azure Monitor (Log Analytics and Event Hub)
- Log Analytics uses KQL for querying audit logs; Event Hub for streaming to SIEM
- `BATCH_COMPLETED_GROUP` captures full SQL text including SELECT statements
- Temporal tables complement SQL Audit but cannot replace it for access logging

---

## Practice Question

**Practice Question**

A security requirement mandates capturing all SELECT statements on the Salaries table including the exact SQL text. Which audit action group captures this?

A. DATABASE_OBJECT_ACCESS_GROUP
B. SCHEMA_OBJECT_ACCESS_GROUP
C. BATCH_COMPLETED_GROUP
D. FAILED_DATABASE_AUTHENTICATION_GROUP

> [!success]- Answer
> **C — BATCH_COMPLETED_GROUP**
>
> BATCH_COMPLETED_GROUP captures all completed T-SQL batches including their SQL text (the `statement` column in audit logs). DATABASE_OBJECT_ACCESS_GROUP (A) and SCHEMA_OBJECT_ACCESS_GROUP (B) track object access events but may not capture the full SQL text of SELECT statements. FAILED_DATABASE_AUTHENTICATION_GROUP (D) captures failed logins only.

---

## Related Topics

- [03-Permissions & Access](./03-permissions-access.md)
- [02-Specialized Tables — Ledger](../01-database-objects/02-specialized-tables.md)
- [03-Monitoring](../08-azure-services-integration/03-monitoring.md)

---

## Official Documentation

- [SQL Server Audit](https://learn.microsoft.com/en-us/sql/relational-databases/security/auditing/sql-server-audit-database-engine)
- [Azure SQL Auditing](https://learn.microsoft.com/en-us/azure/azure-sql/database/auditing-overview)

---

**[← Previous](./03-permissions-access.md) | [↑ Back to Section](./README.md) | [Next →](./05-secure-endpoints.md)**
