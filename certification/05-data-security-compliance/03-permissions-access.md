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

## Permission Hierarchy

```text
Server Level → Database Level → Schema Level → Object Level
    Login         User/Role       Schema perms    GRANT/DENY
```

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

## Passwordless Access — Managed Identity

Managed Identity eliminates the need for credentials by using Azure AD tokens.

### Types of Managed Identity

| Type | Lifecycle | Use Case |
| :--- | :--- | :--- |
| **System-assigned** | Tied to the Azure resource | Single-service authentication |
| **User-assigned** | Independent resource | Multiple services sharing an identity |

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

## Principle of Least Privilege

```sql
-- Bad: granting db_owner to application
ALTER ROLE db_owner ADD MEMBER AppUser;  -- Never do this

-- Good: grant only what's needed
GRANT SELECT ON dbo.Products TO AppUser;
GRANT EXECUTE ON dbo.usp_PlaceOrder TO AppUser;
GRANT INSERT ON dbo.OrderItems TO AppUser;
```

## Ownership Chaining

Ownership chaining allows procedures to access tables owned by the same principal without explicit grants:

```sql
-- If usp_GetCustomerData and dbo.Customers have the same owner,
-- EXECUTE on the procedure implicitly allows access to the table
GRANT EXECUTE ON dbo.usp_GetCustomerData TO ReportUser;
-- ReportUser can now read Customers through the procedure
-- without direct SELECT grant on Customers
```

## Use Cases

- **Managed Identity**: App Services, Azure Functions, ADF pipelines accessing Azure SQL
- **Azure AD Groups**: Manage access by assigning users to AAD groups mapped to DB roles
- **Schema-level grants**: Grant access to all objects in a schema at once for application accounts

## Common Issues & Errors

| Error | Cause | Resolution |
| :--- | :--- | :--- |
| `Login failed for user` | User not mapped to AAD tenant | Create user `FROM EXTERNAL PROVIDER` |
| Managed Identity not working | Resource identity not enabled | Enable System-assigned identity in Azure portal |
| DENY not working | DENY must be on the principal directly | Check role inheritance; DENY on role overrides GRANT on member |

## Exam Tips

- `DENY` always wins — it overrides GRANT even when inherited through a role
- Managed Identity authentication uses `FROM EXTERNAL PROVIDER` syntax in SQL
- Always use **Managed Identity** over connection string credentials for Azure services
- `fn_my_permissions` shows effective permissions for the current user

## Key Takeaways

- SQL Server permission model: GRANT allows, DENY blocks, REVOKE removes
- Azure AD + Managed Identity = passwordless, credential-free authentication
- Principle of least privilege: grant only the permissions required for the task

## Related Topics

- [04-Auditing](./04-auditing.md)
- [05-Secure Endpoints](./05-secure-endpoints.md)
- [03-MCP Server Endpoints](../04-ai-assisted-tools/03-mcp-server-endpoints.md)

## Official Documentation

- [Permissions (Database Engine)](https://learn.microsoft.com/en-us/sql/relational-databases/security/permissions-database-engine)
- [Azure AD Authentication for Azure SQL](https://learn.microsoft.com/en-us/azure/azure-sql/database/authentication-aad-overview)
- [Managed Identity for Azure SQL](https://learn.microsoft.com/en-us/azure/azure-sql/database/authentication-azure-ad-user-assigned-managed-identity)

---

**[← Previous](./02-dynamic-data-masking-rls.md) | [↑ Back to Section](./README.md) | [Next →](./04-auditing.md)**
