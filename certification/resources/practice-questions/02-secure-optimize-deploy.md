---
title: "Practice Questions: Secure, Optimize, and Deploy"
type: practice-questions
tags:
  - dp-800
  - practice-questions
  - secure-optimize-deploy
---

# Practice Questions: Secure, Optimize, and Deploy

Domain 2 covers 35–40% of the DP-800 exam.

---

## Question 1: Always Encrypted — Encryption Type for Filtering

**Question** *(Medium)*:

A security team requires that a `CreditCardNumber` column be encrypted using Always Encrypted. The application must be able to search for records by exact credit card number using a WHERE clause. Which encryption type must be used?

A. RANDOMIZED
B. DETERMINISTIC
C. AES_256_GCM
D. RANDOMIZED with enclave support

> [!success]- Answer
> **B. DETERMINISTIC**
>
> **DETERMINISTIC** encryption always produces the same ciphertext for a given plaintext value, enabling equality-based filtering (`=`, `IN`, `JOIN`, `GROUP BY`) from client applications with the correct column master key.
>
> **RANDOMIZED** produces different ciphertext each time — it cannot be filtered without enclave support. AES_256_GCM is an algorithm, not an Always Encrypted type. RANDOMIZED with enclave support (Always Encrypted with Secure Enclaves) does support filtering but requires additional infrastructure setup.

---

## Question 2: Always Encrypted — Randomized Use Case

**Question** *(Easy)*:

A developer is adding Always Encrypted to a `MedicalNotes nvarchar(max)` column that stores free-text notes and will never be queried with an equality filter. Which encryption type should they choose and why?

A. DETERMINISTIC — because it is always more secure
B. RANDOMIZED — because it provides stronger security and the column doesn't need filtering
C. DETERMINISTIC — because it is required for nvarchar(max) columns
D. RANDOMIZED — because it is the only type that supports large columns

> [!success]- Answer
> **B. RANDOMIZED — because it provides stronger security and the column doesn't need filtering**
>
> RANDOMIZED encryption is preferred when equality filtering is not required. It is cryptographically stronger because identical plaintext values produce different ciphertexts, preventing frequency analysis attacks.
>
> DETERMINISTIC is only necessary when the application needs to filter or join on the encrypted column. Both types support nvarchar(max) columns.

---

## Question 3: Dynamic Data Masking — Default Mask

**Question** *(Easy)*:

A DBA adds a Dynamic Data Masking rule to an `Email nvarchar(256)` column using `MASKED WITH (FUNCTION = 'default()')`. A user without UNMASK permission queries the table. What will they see for a stored value of `alice@contoso.com`?

A. `alice@contoso.com`
B. `xxxx@xxxx.com`
C. `XXXX`
D. `aXXX@XXXX.com`

> [!success]- Answer
> **C. `XXXX`**
>
> The `default()` masking function replaces the entire value with a type-appropriate mask. For string columns (`char`, `nchar`, `varchar`, `nvarchar`), the mask is `XXXX`.
>
> The `email()` function would produce `aXXX@XXXX.com`. Users with the UNMASK permission or `db_owner` membership see the actual value.

---

## Question 4: Dynamic Data Masking — UNMASK Permission

**Question** *(Medium)*:

A reporting user named `ReportUser` needs to see unmasked values in the `PhoneNumber` column, but the column has DDM applied. Other users should continue to see masked values. What is the correct approach?

A. Add `ReportUser` to the `db_datareader` role
B. Grant `ReportUser` the `UNMASK` permission
C. Remove the mask from the column and use a view with masking logic
D. Grant `ReportUser` `SELECT` permission on the column

> [!success]- Answer
> **B. Grant `ReportUser` the `UNMASK` permission**
>
> The `UNMASK` database permission allows a user to see the actual values of masked columns. Syntax: `GRANT UNMASK TO ReportUser;`
>
> `db_datareader` only grants SELECT access but does not bypass masking. `SELECT` permission alone does not bypass DDM. Members of `db_owner` and users with `CONTROL` automatically bypass masking.

---

## Question 5: Row-Level Security — Filter vs Block Predicate

**Question** *(Hard)*:

A developer implements Row-Level Security on a `dbo.Orders` table. Salespeople should only see their own orders in SELECT queries, but they should also be prevented from inserting orders for other salespeople. Which predicates must be configured?

A. One FILTER predicate only
B. One BLOCK predicate only
C. One FILTER predicate and one BLOCK predicate with AFTER INSERT operation
D. Two FILTER predicates — one for SELECT and one for INSERT

> [!success]- Answer
> **C. One FILTER predicate and one BLOCK predicate with AFTER INSERT operation**
>
> - **FILTER predicate**: Silently hides rows that fail the predicate from SELECT, UPDATE, DELETE. Users cannot see or affect rows they don't own.
> - **BLOCK predicate with AFTER INSERT**: Prevents INSERT of rows that would not be visible under the FILTER predicate.
>
> FILTER predicates apply to SELECT/UPDATE/DELETE automatically but do not affect INSERT. A separate BLOCK AFTER INSERT predicate is required to block unauthorized inserts.

---

## Question 6: Row-Level Security — SESSION_CONTEXT

**Question** *(Medium)*:

An application uses a single SQL login for all connections (connection pooling). RLS must enforce that each end user only sees their own rows. The application sets the current user's ID in `SESSION_CONTEXT(N'UserId')` before executing queries. Which approach correctly uses this in an RLS predicate function?

A. `WHERE SalesRepId = USER_NAME()`
B. `WHERE SalesRepId = CAST(SESSION_CONTEXT(N'UserId') AS int)`
C. `WHERE SalesRepId = SYSTEM_USER`
D. `WHERE SalesRepId = SUSER_SNAME()`

> [!success]- Answer
> **B. `WHERE SalesRepId = CAST(SESSION_CONTEXT(N'UserId') AS int)`**
>
> `SESSION_CONTEXT` is the correct mechanism when a single database user (e.g., an application service account) handles all connections. The application calls `EXEC sp_set_session_context N'UserId', @userId` before each query, and the RLS inline TVF reads this value.
>
> `USER_NAME()`, `SYSTEM_USER`, and `SUSER_SNAME()` return the database/login name of the connected SQL user — not useful when all connections share one login.

---

## Question 7: Permission Precedence — DENY Wins

**Question** *(Medium)*:

User `DataAnalyst` is a member of the `Analysts` role, which has been granted `SELECT` on `dbo.SensitiveData`. An administrator also explicitly `DENY`s `SELECT` on `dbo.SensitiveData` to `DataAnalyst` directly. What happens when `DataAnalyst` queries the table?

A. The GRANT from the role takes precedence; the query succeeds
B. The DENY takes precedence; the query fails
C. The most recently applied permission takes precedence
D. Both permissions cancel out; the user has no access

> [!success]- Answer
> **B. The DENY takes precedence; the query fails**
>
> In SQL Server's permission model, **DENY always wins** over GRANT, regardless of whether the GRANT comes from role membership or explicit assignment. This is a fundamental security principle: an explicit denial cannot be overridden by a grant at any level.
>
> To restore access, the administrator must `REVOKE` the DENY (not just add another GRANT). After REVOKE, the role's GRANT will apply.

---

## Question 8: Managed Identity — Connection String

**Question** *(Medium)*:

A developer is configuring an application deployed to Azure App Service to connect to Azure SQL Database using Managed Identity (no password). Which connection string property specifies Managed Identity authentication?

A. `Integrated Security=True`
B. `Authentication=Active Directory Password`
C. `Authentication=Active Directory Managed Identity`
D. `Trusted_Connection=Yes`

> [!success]- Answer
> **C. `Authentication=Active Directory Managed Identity`**
>
> The `Authentication=Active Directory Managed Identity` property in the connection string tells the SQL driver to acquire a token from the Azure Instance Metadata Service (IMDS) using the App Service's managed identity. No password or secret is required.
>
> `Integrated Security=True` uses Windows Authentication (Kerberos/NTLM), which is not applicable in Azure. `Active Directory Password` requires explicit credentials.

---

## Question 9: Managed Identity — External Provider Syntax

**Question** *(Hard)*:

A DBA needs to create a database user for an Azure App Service's system-assigned managed identity in Azure SQL Database. Which T-SQL syntax is correct?

A. `CREATE USER [MyAppService] WITH PASSWORD = 'managed_identity'`
B. `CREATE USER [MyAppService] FROM EXTERNAL PROVIDER`
C. `CREATE LOGIN [MyAppService] FROM EXTERNAL PROVIDER`
D. `CREATE USER [MyAppService] FOR LOGIN [MyAppService]`

> [!success]- Answer
> **B. `CREATE USER [MyAppService] FROM EXTERNAL PROVIDER`**
>
> `FROM EXTERNAL PROVIDER` creates a contained database user backed by Azure Active Directory (Entra ID). The name must exactly match the managed identity's display name in Azure AD.
>
> In Azure SQL Database (not Managed Instance), logins are not supported for Azure AD identities — you create contained users directly. Option C (`CREATE LOGIN`) is used at the server level and is not how Azure AD identities are provisioned in Azure SQL Database.

---

## Question 10: Auditing — Action Groups

**Question** *(Medium)*:

A compliance officer requires that all successful and failed login attempts to Azure SQL Database be captured in the audit log. Which audit action group should be configured?

A. `BATCH_COMPLETED_GROUP`
B. `SUCCESSFUL_DATABASE_AUTHENTICATION_GROUP`
C. `DATABASE_LOGOUT_GROUP`
D. `SUCCESSFUL_LOGIN_GROUP` combined with `FAILED_LOGIN_GROUP`

> [!success]- Answer
> **D. `SUCCESSFUL_LOGIN_GROUP` combined with `FAILED_LOGIN_GROUP`**
>
> - `SUCCESSFUL_LOGIN_GROUP`: Captures successful authentication events.
> - `FAILED_LOGIN_GROUP`: Captures failed authentication attempts.
>
> Both groups together provide complete login audit coverage. `BATCH_COMPLETED_GROUP` captures query execution. These are server-level action groups configured in the database audit policy.

---

## Question 11: Transaction Isolation — RCSI vs Snapshot

**Question** *(Hard)*:

A developer observes that under Read Committed Snapshot Isolation (RCSI), readers don't block writers. A colleague suggests using Snapshot Isolation instead. What is the key difference between RCSI and Snapshot Isolation?

A. RCSI provides statement-level consistency; Snapshot Isolation provides transaction-level consistency
B. RCSI stores versions in tempdb; Snapshot Isolation stores versions in the data files
C. Snapshot Isolation prevents all blocking; RCSI still causes some reader-writer blocking
D. RCSI requires `SET TRANSACTION ISOLATION LEVEL SNAPSHOT` per session; Snapshot Isolation is the default

> [!success]- Answer
> **A. RCSI provides statement-level consistency; Snapshot Isolation provides transaction-level consistency**
>
> - **RCSI**: Each statement sees a consistent view of data as of the start of *that statement*. No code changes required — it replaces the default Read Committed behavior database-wide.
> - **Snapshot Isolation**: Each statement in a transaction sees a consistent view as of the start of *the entire transaction*. Must be explicitly opted into with `SET TRANSACTION ISOLATION LEVEL SNAPSHOT`.
>
> Both use row versioning in tempdb. Snapshot Isolation can detect write conflicts and raise errors; RCSI cannot.

---

## Question 12: Blocking Analysis — DMV

**Question** *(Easy)*:

A DBA suspects a long-running query is blocking other sessions. Which DMV should they query first to identify the blocking chain?

A. `sys.dm_exec_query_stats`
B. `sys.dm_exec_requests`
C. `sys.dm_os_wait_stats`
D. `sys.dm_tran_active_transactions`

> [!success]- Answer
> **B. `sys.dm_exec_requests`**
>
> `sys.dm_exec_requests` shows currently executing requests and includes `blocking_session_id` — the session ID of the session blocking the current request. A `blocking_session_id` > 0 indicates the session is being blocked.
>
> Query: `SELECT session_id, blocking_session_id, wait_type, wait_time, status FROM sys.dm_exec_requests WHERE blocking_session_id > 0`
>
> `sys.dm_os_wait_stats` shows cumulative wait statistics (not per-session). `sys.dm_exec_query_stats` shows historical query performance.

---

## Question 13: Deadlocks — Error and Handling

**Question** *(Medium)*:

An application reports occasional errors with message "Transaction (Process ID XX) was deadlocked on lock resources with another process and has been chosen as the deadlock victim." What error number does this correspond to, and what is the recommended application-level response?

A. Error 1205; retry the transaction after a short delay
B. Error 1205; terminate the application and alert the DBA
C. Error 8621; retry the transaction immediately
D. Error 1205; increase the lock timeout setting

> [!success]- Answer
> **A. Error 1205; retry the transaction after a short delay**
>
> **Error 1205** is the SQL Server deadlock victim error. The deadlock victim's transaction is rolled back automatically, so the application can safely retry it.
>
> Best practice: implement retry logic with a brief exponential backoff (e.g., 100ms, 200ms, 400ms) to avoid immediately re-creating the deadlock. Investigate root cause with the deadlock graph from the system health extended event session or Query Store.

---

## Question 14: Query Execution Plans — Key Lookup

**Question** *(Medium)*:

A developer adds a non-clustered index on `dbo.Orders(OrderDate)` to speed up a query that filters by date and also selects `CustomerName`, `TotalAmount`, and `Status`. The plan still shows a Key Lookup operator. What does this indicate?

A. The non-clustered index is not being used
B. SQL Server must go back to the clustered index to retrieve columns not in the non-clustered index
C. The query is using a hash join instead of a merge join
D. The non-clustered index has too many levels of B-tree

> [!success]- Answer
> **B. SQL Server must go back to the clustered index to retrieve columns not in the non-clustered index**
>
> A **Key Lookup** (or RID Lookup for heap tables) occurs when the non-clustered index satisfies the WHERE clause but does not cover all columns in the SELECT list. SQL Server uses the index to find matching rows, then performs a separate lookup to the clustered index for each row to retrieve the additional columns.
>
> **Fix**: Create a **covering index** by including the additional columns: `CREATE INDEX IX_Orders_Date ON dbo.Orders(OrderDate) INCLUDE (CustomerName, TotalAmount, Status)`.

---

## Question 15: Query Store — Force Plan

**Question** *(Medium)*:

A developer notices that a critical query's performance degraded after a statistics update changed its execution plan. They use Query Store to identify the previously good plan. What action should they take to restore performance without rolling back statistics?

A. Rebuild the index on the table
B. Use `sp_recompile` to force the query to recompile
C. Use Query Store to force the previously good plan
D. Update statistics manually to restore the old plan

> [!success]- Answer
> **C. Use Query Store to force the previously good plan**
>
> Query Store's **Force Plan** feature (`sys.sp_query_store_force_plan`) pins a specific execution plan for a query. The optimizer will use that plan regardless of statistics updates or parameter changes.
>
> In SSMS: Query Store → Regressed Queries → select the query → compare plans → Force Plan. This is the recommended approach for plan regression issues. The forced plan remains until unforced or the query changes significantly.

---

## Question 16: SQL Database Projects — SDK-Style Format

**Question** *(Hard)*:

A team is migrating their SQL Database Project to the SDK-style format. What is the key advantage of SDK-style projects over the legacy `.sqlproj` format?

A. SDK-style projects support a wider range of T-SQL syntax
B. SDK-style projects use MSBuild and support cross-platform builds and NuGet references
C. SDK-style projects produce larger dacpac files with more metadata
D. SDK-style projects eliminate the need for sqlpackage

> [!success]- Answer
> **B. SDK-style projects use MSBuild and support cross-platform builds and NuGet references**
>
> SDK-style `.sqlproj` files (using `Microsoft.Build.Sql` SDK) are:
> - Cross-platform (build on Linux/macOS/Windows)
> - Compatible with `dotnet build`
> - Support NuGet package references for database dependencies
> - Much cleaner project files (auto-include SQL files without explicit entries)
>
> They still produce dacpac files and use sqlpackage for deployment — those tools remain unchanged.

---

## Question 17: DAB — Entity Permissions

**Question** *(Hard)*:

A developer is configuring Data API Builder (DAB) for a public REST API. The `products` entity must allow anonymous GET requests but require authentication for POST. Which configuration section correctly expresses this?

A. Set `authentication.provider` to `Anonymous` globally
B. Configure the entity's `permissions` with `role: anonymous` allowing `read` and `role: authenticated` allowing `create`
C. Set the entity's `rest.enabled: false` and use a custom API
D. Configure `permissions` with `role: anonymous` allowing all CRUD operations

> [!success]- Answer
> **B. Configure the entity's `permissions` with `role: anonymous` allowing `read` and `role: authenticated` allowing `create`**
>
> DAB's permission model is role-based. The built-in `anonymous` role applies to unauthenticated requests; `authenticated` applies to any authenticated user. You configure allowed actions (`read`, `create`, `update`, `delete`) per role per entity.
>
> ```json
> "permissions": [
>   { "role": "anonymous", "actions": ["read"] },
>   { "role": "authenticated", "actions": ["create"] }
> ]
> ```

---

## Question 18: CDC vs Change Tracking

**Question** *(Medium)*:

A downstream application needs to know which rows in `dbo.Inventory` changed since its last sync, but it only needs to know *that* they changed and their current values — not *what* the old values were. Which change capture method is more appropriate and why?

A. CDC — because it captures full before/after images of every change
B. Change Tracking — because it is lightweight, records which rows changed, and the application can query current values directly
C. CDC — because Change Tracking doesn't support DELETE operations
D. Change Tracking — because CDC requires a separate database

> [!success]- Answer
> **B. Change Tracking — because it is lightweight, records which rows changed, and the application can query current values directly**
>
> **Change Tracking** records the primary keys of changed rows and the type of change (INSERT/UPDATE/DELETE). The consumer uses `CHANGETABLE(CHANGES ...)` to get changed PKs and then joins to the source table for current values. It has minimal overhead.
>
> **CDC** captures full before/after row images in change tables — necessary when you need the previous values (e.g., for data warehousing or audit). CDC has higher overhead (log reader agent). Change Tracking does support DELETEs.

---

## Question 19: Azure Monitor — KQL for Audit Logs

**Question** *(Medium)*:

An audit log is being sent to a Log Analytics workspace from Azure SQL Database. A security analyst needs to find all failed login attempts from a specific IP address in the last 7 days. Which KQL query is most appropriate?

A. `AzureDiagnostics | where Category == 'SQLSecurityAuditEvents' | where action_name_s == 'FAILED_LOGIN' | where client_ip_s == '10.0.0.1'`
B. `SecurityEvent | where EventID == 4625 | where IpAddress == '10.0.0.1'`
C. `AzureActivity | where OperationName == 'Login Failed'`
D. `AzureDiagnostics | where ResourceProvider == 'MICROSOFT.SQL' | where succeeded_s == 'false'`

> [!success]- Answer
> **A. `AzureDiagnostics | where Category == 'SQLSecurityAuditEvents' | where action_name_s == 'FAILED_LOGIN' | where client_ip_s == '10.0.0.1'`**
>
> Azure SQL Database audit logs sent to Log Analytics appear in the `AzureDiagnostics` table with `Category = 'SQLSecurityAuditEvents'`. Fields include `action_name_s` (the audit action), `client_ip_s`, `database_principal_name_s`, and `event_time_t`.
>
> Add `| where TimeGenerated > ago(7d)` to restrict to the last 7 days. `SecurityEvent` contains Windows Security events, not SQL audit events.

---

## Question 20: Secrets Management — Key Vault in Pipelines

**Question** *(Hard)*:

A CI/CD pipeline in Azure DevOps needs to retrieve a connection string stored in Azure Key Vault during deployment. The pipeline runs on a Microsoft-hosted agent. What is the recommended approach?

A. Store the connection string as a pipeline variable and reference it with `$(ConnectionString)`
B. Hardcode the connection string in the YAML pipeline file
C. Link the Key Vault to an Azure DevOps variable group using a service connection with appropriate permissions
D. Use the Azure CLI task to call `az keyvault secret show` and echo the value

> [!success]- Answer
> **C. Link the Key Vault to an Azure DevOps variable group using a service connection with appropriate permissions**
>
> The recommended pattern is:
> 1. Create an Azure DevOps **variable group** linked to the Key Vault
> 2. Grant the service connection's service principal `Key Vault Secrets User` role on the vault
> 3. Reference secrets as pipeline variables — they are masked in logs automatically
>
> Hardcoding (option B) is never acceptable. Echoing secret values (option D) risks exposing them in logs. Plain pipeline variables (option A) don't retrieve from Key Vault automatically.

---

**[← Back to Practice Questions](./practice-questions.md)**
