---
title: Object-Level Permissions and Secure Access
type: study-material
tags:
  - dp-800
  - permissions
  - rbac
  - managed-identity
  - passwordless
  - azure-ad
---

# Object-Level Permissions and Secure Access

## Overview

SQL Server uses a layered permission system: server-level logins, database-level users, roles, and object-level GRANT/DENY/REVOKE. Azure SQL extends this with Azure Active Directory authentication and Managed Identity for passwordless access.

> [!abstract]
> - Covers GRANT/DENY/REVOKE, database roles, ownership chaining, and EXECUTE AS context
> - SQL Server uses a hierarchical permission system: server → database → schema → object
> - Key exam topics: DENY/GRANT precedence, fixed database roles, ownership chaining behavior

> [!tip] What the Exam Tests
> - **DENY always wins** over GRANT — even if a GRANT came through role membership, an explicit DENY on the principal blocks access
> - **REVOKE** removes a previously granted or denied permission — it does NOT itself deny access
> - Fixed roles: `db_datareader` = SELECT on all tables; `db_datawriter` = INSERT/UPDATE/DELETE; `db_owner` = full control; `db_ddladmin` = DDL only

---

---

## Permission Hierarchy

```text
Server Level → Database Level → Schema Level → Object Level
    Login         User/Role       Schema perms    GRANT/DENY
```

---

## Server and Database Principals

```sql
-- SQL Login (not recommended for Azure SQL; use AAD)
CREATE LOGIN AppLogin WITH PASSWORD = 'P@ssword123!';

-- Azure AD Login (Azure SQL)
CREATE LOGIN [user@contoso.com] FROM EXTERNAL PROVIDER;

-- Database user mapped to login
CREATE USER AppUser FOR LOGIN AppLogin;

-- Azure AD database user
CREATE USER [app-service-identity] FROM EXTERNAL PROVIDER;

-- User without login (contained database)
CREATE USER ReportUser WITH PASSWORD = 'Report#2025!';
```

---

## Database Roles

```sql
-- Built-in roles
ALTER ROLE db_datareader ADD MEMBER ReportUser;     -- SELECT on all tables/views
ALTER ROLE db_datawriter ADD MEMBER ETLUser;        -- INSERT/UPDATE/DELETE on all tables
ALTER ROLE db_ddladmin   ADD MEMBER SchemaOwner;    -- CREATE/ALTER/DROP objects

-- Custom role
CREATE ROLE OrdersReadOnly;
GRANT SELECT ON SCHEMA::dbo TO OrdersReadOnly;
DENY  SELECT ON dbo.CustomerPayments TO OrdersReadOnly;
ALTER ROLE OrdersReadOnly ADD MEMBER [analyst@contoso.com];
```

---

## Object-Level Permissions

```sql
-- GRANT: explicit allow
GRANT SELECT ON dbo.Customers TO ReportUser;
GRANT EXECUTE ON dbo.usp_GetOrders TO AppUser;
GRANT SELECT, INSERT, UPDATE ON dbo.Orders TO ETLUser;
GRANT VIEW DEFINITION ON dbo.vw_Summary TO ReportUser;

-- DENY: explicit deny (overrides GRANT, including inherited role grants)
DENY SELECT ON dbo.CustomerPayments TO ReportUser;
DENY DELETE ON dbo.Orders TO ReportUser;

-- REVOKE: remove a previously granted or denied permission
REVOKE SELECT ON dbo.Customers FROM ReportUser;

-- Schema-level permissions
GRANT SELECT ON SCHEMA::Reports TO ReportUser;
GRANT EXECUTE ON SCHEMA::dbo TO AppUser;

-- View effective permissions
SELECT * FROM fn_my_permissions('dbo.Orders', 'OBJECT');
SELECT * FROM sys.database_permissions WHERE grantee_principal_id = USER_ID('ReportUser');
```

> [!warning] Common Mistake
> REVOKE ≠ DENY. REVOKE removes a permission entry (the user falls back to inherited permissions). DENY explicitly blocks access. If you GRANT access through a role and then REVOKE from the role, the user may still have access through another path. To explicitly block, use DENY.

---

## Passwordless Access — Managed Identity

**Managed Identity** eliminates the need for credentials by using Azure AD tokens.

### Types of Managed Identity

| Type | Lifecycle | Use Case |
| :--- | :--- | :--- |
| **System-assigned** | Tied to the Azure resource | Single-service authentication |
| **User-assigned** | Independent resource | ==Multiple services sharing an identity== |

### Configuring Managed Identity for Azure SQL

```sql
-- In Azure SQL: create user for the Managed Identity
CREATE USER [my-app-service] FROM EXTERNAL PROVIDER;
ALTER ROLE db_datareader ADD MEMBER [my-app-service];
GRANT EXECUTE ON SCHEMA::dbo TO [my-app-service];
```

```csharp
// Application code — no password needed
var connectionString = "Server=myserver.database.windows.net;Database=mydb;Authentication=Active Directory Managed Identity;";
```

### Azure AD Authentication Methods

| Method | Use Case |
| :--- | :--- |
| `Active Directory Integrated` | Domain-joined machines, SSO |
| `Active Directory Interactive` | MFA-enabled users (prompts) |
| `Active Directory Managed Identity` | Azure-hosted services (System/User assigned) |
| `Active Directory Service Principal` | Apps with client ID + certificate/secret |
| `Active Directory Default` | Tries multiple auth methods in order |

---

## Principle of Least Privilege

```sql
-- Bad: granting db_owner to application
ALTER ROLE db_owner ADD MEMBER AppUser;  -- Never do this

-- Good: grant only what's needed
GRANT SELECT ON dbo.Products TO AppUser;
GRANT EXECUTE ON dbo.usp_PlaceOrder TO AppUser;
GRANT INSERT ON dbo.OrderItems TO AppUser;
```

---

## Contained Database Users

A contained database user has credentials stored in the database itself — no server-level login is required. The user authenticates directly against the database using a password or external provider.

**Benefits:**

- **Portability:** users travel with the database on backup/restore or failover — no orphaned login mapping issues
- **Azure SQL requirement:** Azure SQL does not support traditional SQL logins in the same way; contained users or AAD principals are the recommended pattern
- **Simplified provisioning:** onboard a user without touching the server-level `master` database

**Partial vs. fully contained databases:**

- **Partial containment** — supported in SQL Server on-premises; most features are contained but some server-level dependencies remain
- **Fully contained** — all authentication and metadata are self-contained; not yet widely supported in Azure SQL (uses partial containment model internally)

```sql
-- Enable contained database authentication (on-premises SQL Server)
EXEC sp_configure 'contained database authentication', 1;
RECONFIGURE;

ALTER DATABASE MyDatabase SET CONTAINMENT = PARTIAL;

-- Create contained user (no login required)
USE MyDatabase;
CREATE USER AppUser WITH PASSWORD = 'SecureP@ssword1!';

-- Add to role
ALTER ROLE db_datareader ADD MEMBER AppUser;

-- In Azure SQL: always use contained users
CREATE USER [user@domain.com] FROM EXTERNAL PROVIDER;  -- AAD user
```

---

## EXECUTE AS Context

`EXECUTE AS` temporarily impersonates a different security principal for the duration of a batch or stored procedure. This is used to test permissions, elevate privileges in a controlled way, or run module code as a specific identity.

### Impersonation Contexts

| Context | Scope | Description |
| :--- | :--- | :--- |
| `EXECUTE AS USER` | Database | Impersonate a database user |
| `EXECUTE AS LOGIN` | Server | Impersonate a server login |
| `EXECUTE AS CALLER` | Module | Use caller's identity (default) |
| `EXECUTE AS OWNER` | Module | ==Use the object owner's identity== |
| `EXECUTE AS SELF` | Module | Use the identity of the user who defined the object |

`REVERT` restores the original security context after impersonation.

```sql
-- Impersonate a user for a batch
EXECUTE AS USER = 'ReportingUser';
SELECT * FROM SensitiveView;  -- executes as ReportingUser
REVERT;

-- Procedure runs as its owner (bypasses caller permission check)
CREATE PROCEDURE dbo.sp_SensitiveReport
WITH EXECUTE AS OWNER
AS SELECT * FROM dbo.SalaryData;

-- Check current execution context
SELECT ORIGINAL_LOGIN(), SUSER_SNAME(), USER_NAME();
```

---

## Ownership Chaining

Ownership chaining is a SQL Server mechanism that skips intermediate permission checks when consecutive objects share the same owner.

**Same-owner chain (chain intact):** when a stored procedure and the table it references are both owned by `dbo`, SQL Server does not check SELECT permissions on the table when a user executes the procedure — the call chain is trusted end-to-end.

**Cross-owner chain (chain breaks):** when the procedure owner differs from the table owner, SQL Server enforces a permission check on the table. The caller needs explicit permission on that table in addition to EXECUTE on the procedure.

**Security implication:** granting EXECUTE on a procedure can implicitly provide read access to underlying tables — use this intentionally with `WITH EXECUTE AS OWNER` to bridge a cross-owner chain safely.

```sql
-- Same owner: user needs only EXECUTE on proc, not SELECT on table
-- Both owned by dbo, chain intact
CREATE PROCEDURE dbo.sp_GetOrders AS SELECT * FROM dbo.Orders;
GRANT EXECUTE ON dbo.sp_GetOrders TO RestrictedUser;
-- RestrictedUser can EXEC proc but cannot SELECT from Orders directly

-- Cross-owner: chain breaks, need explicit SELECT too
CREATE PROCEDURE dbo.sp_GetHRData AS SELECT * FROM hr.Employees;
-- User needs EXECUTE on proc AND SELECT on hr.Employees
```

---

## Database vs Server-Level Roles

| Role | Scope | Permissions |
| :--- | :--- | :--- |
| `db_owner` | Database | ==Full control of database== |
| `db_datareader` | Database | SELECT on all tables/views |
| `db_datawriter` | Database | INSERT/UPDATE/DELETE on all tables |
| `db_ddladmin` | Database | CREATE/ALTER/DROP schema objects |
| `db_securityadmin` | Database | Manage roles and permissions |
| `public` | Database | Default permissions for all users |
| `sysadmin` | Server | Full server control |
| `serveradmin` | Server | Server configuration |
| `securityadmin` | Server | Manage server logins |

---

## Use Cases

- **Managed Identity**: App Services, Azure Functions, ADF pipelines accessing Azure SQL
- **Azure AD Groups**: Manage access by assigning users to AAD groups mapped to DB roles
- **Schema-level grants**: Grant access to all objects in a schema at once for application accounts
- **Contained users**: Simplify user management in elastic pools or geo-replicated databases
- **EXECUTE AS OWNER**: Grant controlled access to sensitive tables through procedures without direct table permissions

---

## Common Issues & Errors

| Error | Cause | Resolution |
| :--- | :--- | :--- |
| `Login failed for user` | User not mapped to AAD tenant | Create user `FROM EXTERNAL PROVIDER` |
| Managed Identity not working | Resource identity not enabled | Enable System-assigned identity in Azure portal |
| DENY not working | DENY must be on the principal directly | Check role inheritance; DENY on role overrides GRANT on member |
| Contained user auth fails | Containment not enabled | Run `sp_configure 'contained database authentication', 1` |
| Cross-owner proc fails | Ownership chain broken | Grant explicit table permission or use `WITH EXECUTE AS OWNER` |

---

## Best Practices

- Prefer **Azure AD / Managed Identity** over SQL logins for all Azure-hosted workloads; eliminate stored passwords entirely.
- Use **contained database users** in Azure SQL to avoid orphaned login mappings after failover, restore, or migration.
- Apply `WITH EXECUTE AS OWNER` on stored procedures that access objects across different schemas to control cross-owner chain breaks explicitly rather than granting broad table permissions.
- Avoid placing application identities in `db_owner` or `sysadmin`; grant only the minimum permissions needed per object or schema.
- Audit role membership regularly using `sys.database_role_members` and `sys.server_role_members` — accumulated role grants are a common source of privilege creep.

---

## Exam Tips

> [!tip] Exam Tips
> - `DENY` always wins — it overrides GRANT even when inherited through a role
> - Managed Identity authentication uses `FROM EXTERNAL PROVIDER` syntax in SQL
> - Always use **Managed Identity** over connection string credentials for Azure services
> - `fn_my_permissions` shows effective permissions for the current user
> - Ownership chaining skips permission checks only when **consecutive objects share the same owner** — a different owner breaks the chain
> - `EXECUTE AS OWNER` is the standard fix for cross-owner chain breaks
> - Contained database users require `SET CONTAINMENT = PARTIAL` on on-premises SQL Server; Azure SQL uses partial containment by default

---

## Key Takeaways

- SQL Server permission model: GRANT allows, DENY blocks, REVOKE removes
- Azure AD + Managed Identity = passwordless, credential-free authentication
- Principle of least privilege: grant only the permissions required for the task
- Contained users travel with the database; no server-level login dependency
- Ownership chaining reduces permission grants but breaks across different owners
- `EXECUTE AS` enables controlled impersonation; always `REVERT` after use

---

## Practice Questions

**Practice Question**

A stored procedure owned by `dbo` calls a table owned by `hr_schema`. A user has EXECUTE permission on the procedure but no explicit permissions on `hr_schema.Employees`. What happens when the user runs the procedure?

A. The procedure executes successfully due to ownership chaining
B. The procedure fails because ownership chaining only works within the same schema
C. The procedure fails because the chain breaks across different owners
D. The procedure runs only if the user has db_datareader role

> [!success]- Answer
> **C — The procedure fails because the chain breaks across different owners**
>
> Ownership chaining only skips permission checks when the calling object and the called object share the same owner. When the procedure (owned by `dbo`) calls a table owned by a different principal (`hr_schema` owner), the chain breaks and the caller needs explicit permission on the table. To fix: use `WITH EXECUTE AS OWNER` on the procedure, grant the table permission to the procedure's owner, or grant the permission directly to the user.

---

## Related Topics

- [04-Auditing](./04-auditing.md)
- [05-Secure Endpoints](./05-secure-endpoints.md)
- [03-MCP Server Endpoints](../04-ai-assisted-tools/03-mcp-server-endpoints.md)

---

## Official Documentation

- [Permissions (Database Engine)](https://learn.microsoft.com/en-us/sql/relational-databases/security/permissions-database-engine)
- [Azure AD Authentication for Azure SQL](https://learn.microsoft.com/en-us/azure/azure-sql/database/authentication-aad-overview)
- [Managed Identity for Azure SQL](https://learn.microsoft.com/en-us/azure/azure-sql/database/authentication-azure-ad-user-assigned-managed-identity)
- [Contained Database Users](https://learn.microsoft.com/en-us/sql/relational-databases/security/contained-database-users-making-your-database-portable)
- [EXECUTE AS (Transact-SQL)](https://learn.microsoft.com/en-us/sql/t-sql/statements/execute-as-transact-sql)
- [Ownership Chaining](https://learn.microsoft.com/en-us/sql/relational-databases/security/ownership-and-user-schema-separation)

---

**[← Previous](./02-dynamic-data-masking-rls.md) | [↑ Back to Section](./data-security-compliance.md) | [Next →](./04-auditing.md)**
