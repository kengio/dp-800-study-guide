---
title: Security Implementation Patterns
type: code-examples
tags:
  - dp-800
  - tsql
  - code-examples
  - security
  - rls
  - data-masking
  - permissions
---

# Security Implementation Patterns

T-SQL patterns for implementing Row-Level Security, Dynamic Data Masking, permissions,
ownership chaining, and Always Encrypted — all exam-relevant for DP-800 Domain 2.

> [!abstract] What You'll Learn
> - Row-Level Security with filter and block predicates for multi-tenant isolation
> - Dynamic Data Masking with all four masking functions
> - Permission management patterns with GRANT, DENY, REVOKE, and roles
> - Ownership chaining and Always Encrypted key hierarchy

## Table of Contents

- [[#Row-Level Security — Filter Predicates]]
- [[#Row-Level Security — Block Predicates]]
- [[#Dynamic Data Masking]]
- [[#Permission Management — GRANT / DENY / REVOKE]]
- [[#Ownership Chaining]]
- [[#Always Encrypted — Key Hierarchy]]

---

## Row-Level Security — Filter Predicates

> [!info] Use filter predicates to silently restrict row visibility per user or tenant without changing application queries.

Filter predicates silently restrict which rows a user can read (SELECT) or write (INSERT/UPDATE/DELETE).
The predicate function returns a table; rows are included only when the function returns a row.

```sql
-- Prerequisites: dedicated schema for security objects
CREATE SCHEMA Security;
GO

-- ── Single-tenant HR example ──────────────────────────────────────────────────
-- Users see only rows belonging to their own department.
-- USER_NAME() returns the database user name of the current connection.

CREATE FUNCTION Security.fn_DepartmentFilter(@DepartmentName NVARCHAR(100))
RETURNS TABLE
WITH SCHEMABINDING                          -- required for RLS predicates
AS
RETURN
    SELECT 1 AS fn_result
    WHERE @DepartmentName = USER_NAME()     -- row's dept matches current user name
       OR IS_MEMBER('db_owner') = 1;        -- db_owner bypasses the filter
GO

-- Apply the filter to the Employees table
CREATE SECURITY POLICY HR.DepartmentPolicy
ADD FILTER PREDICATE Security.fn_DepartmentFilter(Department)
ON dbo.Employees
WITH (STATE = ON);
GO

-- ── Multi-tenant example using SESSION_CONTEXT ────────────────────────────────
-- TenantID is injected at login time via sp_set_session_context.
-- SESSION_CONTEXT is a safe, read-only key/value store per connection.

CREATE FUNCTION Security.fn_TenantFilter(@TenantID INT)
RETURNS TABLE
WITH SCHEMABINDING
AS
RETURN
    SELECT 1 AS result
    WHERE @TenantID = CAST(SESSION_CONTEXT(N'TenantID') AS INT)
       OR IS_MEMBER('db_owner') = 1;        -- admins see all tenants
GO

-- Apply the policy to the Orders table
CREATE SECURITY POLICY dbo.TenantPolicy
ADD FILTER PREDICATE Security.fn_TenantFilter(TenantID)
ON dbo.Orders
WITH (STATE = ON);
GO

-- ── Setting session context at application login ──────────────────────────────
-- Application layer (or login trigger) sets the tenant before any queries run.
EXEC sp_set_session_context N'TenantID', 42, @read_only = 1;
-- @read_only = 1 prevents the application from overwriting the value mid-session

-- ── Testing with EXECUTE AS ───────────────────────────────────────────────────
-- Impersonate a specific database user to verify the predicate works correctly.
EXECUTE AS USER = 'tenant_user_42';

SELECT * FROM dbo.Orders;   -- returns only TenantID = 42 rows

REVERT;                     -- always revert after testing
```

> [!warning] Watch Out
> Filter predicates fail silently (return 0 rows instead of an error). Always test with `EXECUTE AS` to verify the predicate returns the correct rows for each user context.

---

## Row-Level Security — Block Predicates

> [!info] Use block predicates to prevent users from writing rows that violate the security policy.

Block predicates prevent write operations that violate the security policy.
They complement filter predicates, which only restrict reads.

```sql
-- Block predicate types:
--   AFTER INSERT  — prevents inserting a row the user cannot see
--   AFTER UPDATE  — prevents updating a row so that the user could no longer see it
--   BEFORE UPDATE — prevents updating a row the user currently cannot see
--   BEFORE DELETE — prevents deleting a row the user currently cannot see

-- Reuse the same predicate function defined above (fn_TenantFilter)

-- ── Add block predicates to the existing tenant policy ────────────────────────
-- Must disable the policy to alter it, then re-enable.
ALTER SECURITY POLICY dbo.TenantPolicy
ADD BLOCK PREDICATE Security.fn_TenantFilter(TenantID)
ON dbo.Orders AFTER INSERT;         -- cannot INSERT a row for a different tenant

ALTER SECURITY POLICY dbo.TenantPolicy
ADD BLOCK PREDICATE Security.fn_TenantFilter(TenantID)
ON dbo.Orders AFTER UPDATE;         -- cannot UPDATE a row so it belongs to another tenant

ALTER SECURITY POLICY dbo.TenantPolicy
ADD BLOCK PREDICATE Security.fn_TenantFilter(TenantID)
ON dbo.Orders BEFORE UPDATE;        -- cannot UPDATE a row you cannot see

ALTER SECURITY POLICY dbo.TenantPolicy
ADD BLOCK PREDICATE Security.fn_TenantFilter(TenantID)
ON dbo.Orders BEFORE DELETE;        -- cannot DELETE a row you cannot see
GO

-- ── Temporarily disable a policy (e.g., bulk load by admin) ──────────────────
ALTER SECURITY POLICY dbo.TenantPolicy WITH (STATE = OFF);
-- ... perform bulk operation ...
ALTER SECURITY POLICY dbo.TenantPolicy WITH (STATE = ON);
GO

-- ── Drop a security policy entirely ──────────────────────────────────────────
DROP SECURITY POLICY dbo.TenantPolicy;

-- Block violations raise error 33504 (AFTER) or 33505 (BEFORE).
-- Filter violations return 0 rows silently — no error is raised.
```

---

## Dynamic Data Masking

> [!info] Use DDM to obfuscate sensitive column values for unprivileged users without changing stored data.

Dynamic Data Masking (DDM) obfuscates sensitive column values for unprivileged users.
Privileged users (db_owner, users granted UNMASK) always see the real data.

```sql
-- ── All four masking functions ────────────────────────────────────────────────

-- default()   — full mask based on data type
--               NVARCHAR/VARCHAR → XXXX
--               numeric types   → 0
--               date/time       → 1900-01-01 00:00:00.0000000
--               binary types    → single zero byte

-- email()     — exposes first letter + masks domain: aXXX@XXXX.com

-- random(low, high) — substitutes a random integer between low and high
--                     only for numeric columns

-- partial(prefix_len, padding, suffix_len)
--               — exposes N chars from the start, N chars from the end,
--                 fills the middle with the padding string

CREATE TABLE dbo.Customers (
    CustomerID  INT           PRIMARY KEY,
    Name        NVARCHAR(100) MASKED WITH (FUNCTION = 'default()'),
                                            -- masked: 'XXXX'
    Email       NVARCHAR(200) MASKED WITH (FUNCTION = 'email()'),
                                            -- masked: 'jXXX@XXXX.com'
    Phone       NVARCHAR(20)  MASKED WITH (FUNCTION = 'partial(2,"XXX-XXXX-",2)'),
                                            -- e.g. '0412-345-678' → '04XXX-XXXX-78'
    CreditScore INT           MASKED WITH (FUNCTION = 'random(300, 850)'),
                                            -- masked: random int 300–850
    SSN         NVARCHAR(11)  MASKED WITH (FUNCTION = 'default()')
                                            -- masked: 'XXXX'
);
GO

-- ── Add masking to an existing column ────────────────────────────────────────
ALTER TABLE dbo.Customers
ALTER COLUMN SSN NVARCHAR(11) MASKED WITH (FUNCTION = 'default()');

-- ── Remove masking from a column ─────────────────────────────────────────────
ALTER TABLE dbo.Customers
ALTER COLUMN CreditScore INT;   -- omit MASKED clause to drop the mask

-- ── Grant unmask permission to privileged users / roles ───────────────────────
GRANT UNMASK TO DataAnalystRole;    -- role sees real data
GRANT UNMASK TO [domain\senior_analyst];

-- Revoke unmask if privilege no longer needed
REVOKE UNMASK FROM DataAnalystRole;

-- ── Verify masking behaviour ─────────────────────────────────────────────────
-- As a low-privilege user:
EXECUTE AS USER = 'low_priv_user';
SELECT CustomerID, Name, Email, Phone, CreditScore FROM dbo.Customers;
-- Name → 'XXXX', Email → 'jXXX@XXXX.com', CreditScore → random value
REVERT;

-- DDM does NOT encrypt data at rest; it only alters query result presentation.
-- Determined users with ALTER TABLE permission can remove masks — use RLS + DDM together.
```

**Masked output** (as `low_priv_user`):

| CustomerID | Name | Email | Phone | CreditScore |
|---|---|---|---|---|
| 1 | XXXX | jXXX@XXXX.com | 04XXX-XXXX-78 | 617 |

> [!warning] Watch Out
> DDM can be bypassed by users with `db_owner` or `ALTER TABLE` permissions — they can simply remove masks. Combine DDM with RLS for defense in depth.

> [!tip] Exam Tip
> DDM does **not** encrypt data at rest — it only alters query result presentation. Users with ALTER TABLE can remove masks. The exam tests awareness of this limitation.

---

## Permission Management — GRANT / DENY / REVOKE

> [!info] Use GRANT/DENY/REVOKE to control object and schema-level access, remembering that DENY always overrides GRANT.

The T-SQL permission model: GRANT gives access, DENY explicitly refuses access (overrides GRANT),
REVOKE removes a previously granted or denied permission (neither allows nor denies).

```sql
-- ── Object-level permissions ──────────────────────────────────────────────────
GRANT  SELECT              ON dbo.Products         TO SalesRole;
GRANT  INSERT, UPDATE      ON dbo.Orders           TO SalesRole;
GRANT  DELETE              ON dbo.Orders           TO ManagerRole;
GRANT  EXECUTE             ON dbo.sp_ProcessOrder  TO SalesRole;

-- DENY overrides any GRANT — even if the user is in a role that has GRANT
DENY   SELECT              ON dbo.Salaries         TO SalesRole;

-- REVOKE removes a specific GRANT or DENY (does not imply the opposite)
REVOKE INSERT              ON dbo.Orders           FROM SalesRole;

-- ── Schema-level permissions (cascades to all objects in the schema) ──────────
GRANT  SELECT ON SCHEMA::dbo        TO ReportingRole;
DENY   SELECT ON SCHEMA::Payroll    TO ReportingRole;  -- override for sensitive schema

-- ── WITH GRANT OPTION — allows the grantee to re-grant the permission ─────────
GRANT  SELECT ON dbo.Products TO TeamLead WITH GRANT OPTION;
-- TeamLead can now run: GRANT SELECT ON dbo.Products TO SomeOtherUser;

-- ── Database-level roles ──────────────────────────────────────────────────────
CREATE ROLE ReportingRole;
CREATE ROLE SalesRole;
CREATE ROLE ManagerRole;

-- Add members to roles
ALTER ROLE ReportingRole ADD MEMBER [domain\analyst1];
ALTER ROLE SalesRole     ADD MEMBER [domain\sales_rep];
ALTER ROLE ManagerRole   ADD MEMBER [domain\mgr_jones];

-- Remove a member from a role
ALTER ROLE SalesRole DROP MEMBER [domain\sales_rep];

-- ── Reporting role pattern: read-all, block sensitive ────────────────────────
GRANT SELECT ON SCHEMA::dbo          TO ReportingRole;  -- all objects in dbo
DENY  SELECT ON dbo.Salaries         TO ReportingRole;  -- override for sensitive table
DENY  SELECT ON dbo.EmployeeSSN      TO ReportingRole;
GRANT EXECUTE ON dbo.sp_GetSummary   TO ReportingRole;  -- allow specific procs

-- ── View effective permissions ────────────────────────────────────────────────
SELECT * FROM fn_my_permissions(NULL, 'DATABASE');          -- current user, db-level
SELECT * FROM fn_my_permissions('dbo.Orders', 'OBJECT');    -- current user, object-level
SELECT HAS_PERMS_BY_NAME('dbo.Orders', 'OBJECT', 'SELECT'); -- 1 = yes, 0 = no
```

> [!tip] Exam Tip
> DENY **always** overrides GRANT, even through role membership. If a user's role has GRANT SELECT but the user has DENY SELECT, the DENY wins. The exam tests this precedence order.

---

## Ownership Chaining

> [!info] Use ownership chaining to avoid granting direct table permissions when stored procedures and tables share the same owner.

Ownership chaining allows SQL Server to skip intermediate permission checks when all objects
in a call chain share the same owner. When the owner changes, the chain breaks and explicit
permissions are required on the referenced object.

```sql
-- ── Chain intact: proc and table both owned by dbo ────────────────────────────
-- User only needs EXECUTE on sp_GetOrders; SELECT on dbo.Orders is NOT checked.
CREATE PROCEDURE dbo.sp_GetOrders
AS
    SELECT OrderID, CustomerID, TotalAmount
    FROM dbo.Orders;       -- same owner (dbo) → chain applies
GO

GRANT EXECUTE ON dbo.sp_GetOrders TO ReportingRole;
-- ReportingRole can call sp_GetOrders without SELECT on dbo.Orders

-- ── Chain broken: proc in dbo, table in different schema/owner ────────────────
-- User needs both EXECUTE on the proc AND SELECT on other_schema.SensitiveTable.
CREATE PROCEDURE dbo.sp_CrossSchema
AS
    SELECT * FROM other_schema.SensitiveTable;  -- different owner → chain breaks
GO

-- ── Workaround: EXECUTE AS to safely bridge the ownership gap ─────────────────
-- EXECUTE AS OWNER: proc runs as the proc owner (dbo), which does own SensitiveTable
--                   or has been granted access.
CREATE PROCEDURE dbo.sp_CrossSchemaSafe
WITH EXECUTE AS OWNER          -- impersonate proc owner during execution
AS
    SELECT * FROM other_schema.SensitiveTable;
GO

-- EXECUTE AS 'SpecificUser': useful when a dedicated service account owns objects
CREATE PROCEDURE dbo.sp_AdminTask
WITH EXECUTE AS 'svc_dbadmin'  -- impersonate a named database user
AS
    DELETE FROM dbo.AuditLog WHERE LogDate < DATEADD(YEAR, -7, GETDATE());
GO

-- ── EXECUTE AS CALLER (default) vs EXECUTE AS SELF ───────────────────────────
-- CALLER (default): permission checks use the calling user's context
-- SELF:             permission checks use the user who created the procedure
-- OWNER:            permission checks use the proc owner's context
-- 'username':       permission checks use the named user's context
```

---

## Always Encrypted — Key Hierarchy

> [!info] Use Always Encrypted when the database engine and DBAs must never see plaintext values — only client applications with the CMK can decrypt.

Always Encrypted protects sensitive columns so that only client applications with access to
the Column Master Key (CMK) can read plaintext values. The database engine and DBAs see only
ciphertext.

Key hierarchy:
- **Column Master Key (CMK):** asymmetric key stored externally (Azure Key Vault, Windows
  Certificate Store, HSM). SQL Server stores only metadata (key store + path).
- **Column Encryption Key (CEK):** symmetric key stored in the database, encrypted by the CMK.
  Each encrypted column references one CEK.

```sql
-- ── Step 1: Create Column Master Key metadata ─────────────────────────────────
-- The actual key material lives in Azure Key Vault.
-- SQL Server stores only the provider name and key path.
CREATE COLUMN MASTER KEY MyCMK
WITH (
    KEY_STORE_PROVIDER_NAME = 'AZURE_KEY_VAULT',
    KEY_PATH = 'https://mykeyvault.vault.azure.net/keys/MyCMK/abc123def456'
);
GO

-- Windows Certificate Store alternative (for dev/test):
CREATE COLUMN MASTER KEY DevCMK
WITH (
    KEY_STORE_PROVIDER_NAME = 'MSSQL_CERTIFICATE_STORE',
    KEY_PATH = 'CurrentUser/My/THUMBPRINT_GOES_HERE'
);
GO

-- ── Step 2: Create Column Encryption Key ─────────────────────────────────────
-- ENCRYPTED_VALUE is generated by SSMS or the SqlServer PowerShell module:
--   New-SqlColumnEncryptionKeyEncryptedValue
-- The engine never sees the plaintext CEK value.
CREATE COLUMN ENCRYPTION KEY MyCEK
WITH VALUES (
    COLUMN_MASTER_KEY = MyCMK,
    ALGORITHM        = 'RSA_OAEP',
    ENCRYPTED_VALUE  = 0x016E...   -- truncated; real value is ~700 hex bytes
);
GO

-- ── Step 3: Create table with encrypted columns ───────────────────────────────
-- Encryption types:
--   DETERMINISTIC — same plaintext → same ciphertext; supports equality predicates (=, IN)
--                   and JOIN; weaker against frequency analysis attacks
--   RANDOMIZED    — same plaintext → different ciphertext each time; stronger security
--                   but cannot be used in WHERE clauses or as JOIN keys
CREATE TABLE dbo.Patients (
    PatientID    INT           PRIMARY KEY,
    LastName     NVARCHAR(100) NOT NULL,

    -- Deterministic: allows WHERE SSN = @param lookups
    SSN          NVARCHAR(11)
        ENCRYPTED WITH (
            ENCRYPTION_TYPE       = DETERMINISTIC,
            ALGORITHM             = 'AEAD_AES_256_CBC_HMAC_SHA_256',
            COLUMN_ENCRYPTION_KEY = MyCEK
        ),

    -- Randomized: stronger; cannot appear in WHERE / GROUP BY / JOIN
    MedicalNotes NVARCHAR(MAX)
        ENCRYPTED WITH (
            ENCRYPTION_TYPE       = RANDOMIZED,
            ALGORITHM             = 'AEAD_AES_256_CBC_HMAC_SHA_256',
            COLUMN_ENCRYPTION_KEY = MyCEK
        ),

    -- Deterministic on an INT: supports equality queries via parameterized queries (not range queries)
    DiagnosisCode INT
        ENCRYPTED WITH (
            ENCRYPTION_TYPE       = DETERMINISTIC,
            ALGORITHM             = 'AEAD_AES_256_CBC_HMAC_SHA_256',
            COLUMN_ENCRYPTION_KEY = MyCEK
        )
);
GO

-- ── Querying encrypted columns ────────────────────────────────────────────────
-- Requires Column Encryption Setting=Enabled in the connection string.
-- The driver encrypts @ssn before sending to the server; server compares ciphertext.
-- This only works with DETERMINISTIC encryption.

-- Connection string: "Column Encryption Setting=Enabled;"

DECLARE @ssn NVARCHAR(11) = '123-45-6789';
SELECT PatientID, LastName
FROM dbo.Patients
WHERE SSN = @ssn;   -- parameterized query — driver handles encryption transparently

-- ── Key rotation: create new CMK, re-encrypt CEK, update metadata ─────────────
-- Done via SSMS wizard or PowerShell (Invoke-SqlColumnMasterKeyRotation).
-- No schema changes needed for the table columns.
```

> [!tip] Exam Tip
> DETERMINISTIC encryption supports equality predicates (`=`, `IN`, `JOIN`) but **not** range queries (`>`, `<`, `BETWEEN`). RANDOMIZED encryption supports **neither** — it is display-only. The exam tests which operations each encryption type allows.

---

**[← Back to Code Examples](./README.md) | [↑ Back to Certification](../../../README.md)**
