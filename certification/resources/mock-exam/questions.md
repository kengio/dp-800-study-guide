---
title: "DP-800 Mock Exam 1 — Questions"
type: practice-questions
tags:
  - dp-800
  - mock-exam
---

# DP-800 Mock Exam 1 — Questions

Complete all 45 questions before checking answers. Time limit: 60 minutes.

---

<!-- DOMAIN 1: Design and Develop (~17 questions) -->

## Question 1: Columnstore Index for Analytics *(Medium)*

A data engineering team is building a reporting table that will receive nightly bulk loads and support exclusively analytical queries. Which index type maximizes compression and analytical query performance?

A. Clustered B-tree index on the load date column
B. Non-clustered columnstore index added alongside the heap
C. Clustered columnstore index
D. Multiple non-clustered B-tree indexes on each report dimension

> [!success]- Answer
> **C. Clustered columnstore index**
>
> A clustered columnstore index (CCI) is the optimal choice for exclusively analytical workloads. It replaces the rowstore, stores data column-by-column for maximum compression (5–10x typical), and enables batch mode execution which processes ~900 rows per CPU batch. For nightly bulk loads, the delta rowstore efficiently absorbs inserts before compressing into column segments.

---

## Question 2: Temporal Table — Point-in-Time Query *(Easy)*

A developer needs to see the state of the `dbo.Contracts` temporal table as it appeared on March 1, 2025 at noon UTC. Which syntax is correct?

A. `SELECT * FROM dbo.Contracts WHERE SysStartTime <= '2025-03-01 12:00:00'`
B. `SELECT * FROM dbo.Contracts FOR SYSTEM_TIME AS OF '2025-03-01T12:00:00'`
C. `SELECT * FROM dbo.Contracts FOR SYSTEM_TIME ALL WHERE SysStartTime = '2025-03-01 12:00:00'`
D. `SELECT * FROM dbo.ContractsHistory WHERE SysEndTime > '2025-03-01 12:00:00'`

> [!success]- Answer
> **B. `SELECT * FROM dbo.Contracts FOR SYSTEM_TIME AS OF '2025-03-01T12:00:00'`**
>
> `FOR SYSTEM_TIME AS OF` is the cleanest and most correct approach. SQL Server automatically queries both the current and history tables and returns rows that were active at the specified timestamp — no manual WHERE logic required.

---

## Question 3: JSON_VALUE vs JSON_QUERY *(Easy)*

A column stores `{"product":{"name":"Laptop","specs":{"ram":16}}}`. A developer wants to return the `specs` object as a JSON fragment. Which function is correct?

A. `JSON_VALUE(col, '$.product.specs')`
B. `JSON_QUERY(col, '$.product.specs')`
C. `JSON_MODIFY(col, '$.product.specs', NULL)`
D. `OPENJSON(col, '$.product.specs')`

> [!success]- Answer
> **B. `JSON_QUERY(col, '$.product.specs')`**
>
> `JSON_QUERY` returns objects and arrays (JSON fragments) from a JSON path. `JSON_VALUE` returns scalar primitive values (strings, numbers, booleans) and returns NULL when pointed at an object. Since `specs` is an object `{"ram":16}`, `JSON_QUERY` is required.

---

## Question 4: Window Function Frame *(Medium)*

A developer wants a 3-row moving average of `DailySales` ordered by `SaleDate`. Which OVER clause is correct?

A. `AVG(DailySales) OVER (ORDER BY SaleDate ROWS BETWEEN 2 PRECEDING AND CURRENT ROW)`
B. `AVG(DailySales) OVER (ORDER BY SaleDate RANGE BETWEEN 2 PRECEDING AND CURRENT ROW)`
C. `AVG(DailySales) OVER (ORDER BY SaleDate ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)`
D. `AVG(DailySales) OVER (PARTITION BY SaleDate)`

> [!success]- Answer
> **A. `AVG(DailySales) OVER (ORDER BY SaleDate ROWS BETWEEN 2 PRECEDING AND CURRENT ROW)`**
>
> `ROWS BETWEEN 2 PRECEDING AND CURRENT ROW` defines a physical 3-row frame (current row plus the 2 rows before it). `RANGE` uses logical ranges based on values, not physical row counts, and would not give a consistent 3-row window when dates are not uniformly spaced. Option C gives a running average from the beginning.

---

## Question 5: Partition Function — RANGE LEFT *(Hard)*

A partition function is defined as `CREATE PARTITION FUNCTION PF (date) AS RANGE LEFT FOR VALUES ('2025-01-01', '2025-02-01')`. Which partition contains a row with value `'2025-01-01'`?

A. Partition 1 (values before 2025-01-01)
B. Partition 2 (January 2025)
C. Partition 3 (values on/after 2025-02-01)
D. Partition 1 (because RANGE LEFT places the boundary in the left partition)

> [!success]- Answer
> **D. Partition 1 (because RANGE LEFT places the boundary in the left partition)**
>
> With `RANGE LEFT`, the boundary value belongs to the **left** (lower) partition. So `'2025-01-01'` belongs to partition 1 (values <= `'2025-01-01'`). Partition 2 holds values > `'2025-01-01'` AND <= `'2025-02-01'`. This is the opposite of `RANGE RIGHT`, where the boundary value is the first value in the right partition.

---

## Question 6: Recursive CTE — Termination *(Medium)*

A recursive CTE traversing an employee hierarchy is returning error "Maximum recursion 100 has been exhausted." The data has no circular references. What is the most appropriate fix?

A. Change `UNION ALL` to `UNION` to prevent duplicates
B. Add `OPTION (MAXRECURSION 0)` if the hierarchy legitimately exceeds 100 levels, after verifying no circular references exist
C. Remove the WHERE clause from the anchor member
D. Replace the recursive CTE with a WHILE loop

> [!success]- Answer
> **B. Add `OPTION (MAXRECURSION 0)` if the hierarchy legitimately exceeds 100 levels, after verifying no circular references exist**
>
> The default MAXRECURSION is 100 as a safety guard against infinite loops. If the hierarchy legitimately has more than 100 levels and there are confirmed no circular references, `OPTION (MAXRECURSION 0)` removes the limit. Always verify data integrity before doing this.

---

## Question 7: Indexed View Requirements *(Hard)*

A developer attempts to create an indexed view with `GROUP BY` but gets an error. Which two conditions are required for the view to be indexable?

A. The view must use `WITH SCHEMABINDING` and the first index must be a unique clustered index
B. The view must use `WITH ENCRYPTION` and include a primary key
C. The view must include `COUNT_BIG(*)` and use `WITH SCHEMABINDING`
D. The first index must be non-clustered unique and the view must reference only one table

> [!success]- Answer
> **A. The view must use `WITH SCHEMABINDING` and the first index must be a unique clustered index**
>
> Indexed views require: (1) `WITH SCHEMABINDING` to prevent schema changes to underlying tables, and (2) the first index must be a `UNIQUE CLUSTERED` index. Additionally, views with `GROUP BY` must use `COUNT_BIG(*)` (not `COUNT(*)`), but A correctly identifies the two core structural requirements.

---

## Question 8: Graph Tables — MATCH Syntax *(Medium)*

Node tables `User` and `Product` exist along with an edge table `Purchased`. Which query finds all products purchased by users who follow Alice?

A. `MATCH(alice-(Purchased)->user-(follows)->product)`
B. `MATCH(alice-(follows)->user-(Purchased)->product)`
C. `MATCH(alice<-(follows)-user AND user-(Purchased)->product)`
D. `MATCH(alice, follows, user, Purchased, product)`

> [!success]- Answer
> **B. `MATCH(alice-(follows)->user-(Purchased)->product)`**
>
> MATCH uses `node-(edge)->node` syntax chained together for multi-hop traversal. Alice follows users (`alice-(follows)->user`), and those users purchased products (`user-(Purchased)->product`). The chain reads left to right following directed edges.

---

## Question 9: NOT EXISTS vs NOT IN *(Medium)*

A developer writes `WHERE ProductId NOT IN (SELECT ProductId FROM dbo.Discontinued)` and gets zero rows despite expecting results. The most likely cause is:

A. The subquery returns more than 1000 rows
B. A NULL exists in the `ProductId` column of `dbo.Discontinued`
C. `NOT IN` requires an index on `ProductId`
D. The data types of `ProductId` in both tables differ

> [!success]- Answer
> **B. A NULL exists in the `ProductId` column of `dbo.Discontinued`**
>
> When a subquery used with `NOT IN` returns any NULL value, the entire `NOT IN` predicate evaluates to UNKNOWN for every row (because `x <> NULL` is UNKNOWN, not TRUE). The fix is to use `NOT EXISTS` which correctly handles NULLs, or add `WHERE ProductId IS NOT NULL` to the subquery.

---

## Question 10: Scalar UDF Performance *(Easy)*

A scalar UDF is called in a SELECT list against a 100-million-row table. Performance is unacceptably slow. What is the primary reason?

A. Scalar UDFs do not support indexes
B. Scalar UDFs execute once per row and prevent parallelism in the query plan
C. Scalar UDFs require explicit transactions
D. The function is not compiled to native code

> [!success]- Answer
> **B. Scalar UDFs execute once per row and prevent parallelism in the query plan**
>
> Traditional T-SQL scalar UDFs force serial execution and are invoked once per row, creating massive overhead on large tables. Alternatives include: inline table-valued functions (which the optimizer can inline), computed columns, or inlining the expression directly. SQL Server 2019+ can automatically inline some simple scalar UDFs.

---

## Question 11: Ledger Table — Append-Only *(Medium)*

A financial auditing system requires a table where records can never be deleted or modified after insertion, enforced at the engine level. Which CREATE TABLE option achieves this?

A. `WITH (SYSTEM_VERSIONING = ON)`
B. `WITH (LEDGER = ON, APPEND_ONLY = ON)`
C. `WITH (LEDGER = ON)` (updatable ledger)
D. Adding a trigger that raises an error on DELETE

> [!success]- Answer
> **B. `WITH (LEDGER = ON, APPEND_ONLY = ON)`**
>
> Append-only ledger tables block UPDATE and DELETE at the storage engine level — not through triggers that can be disabled. They maintain a cryptographically linked hash chain verified by `sys.sp_verify_database_ledger`. Updatable ledger tables allow modifications but log all changes with cryptographic proof.

---

## Question 12: JSON Aggregation — JSON_ARRAYAGG *(Easy)*

A developer needs to aggregate product names into a JSON array per category using `JSON_ARRAYAGG`. On which minimum version is this available?

A. SQL Server 2016
B. SQL Server 2019
C. SQL Server 2022 / Azure SQL Database
D. SQL Server 2017

> [!success]- Answer
> **C. SQL Server 2022 / Azure SQL Database**
>
> `JSON_ARRAYAGG` and `JSON_OBJECTAGG` were introduced in SQL Server 2022 and Azure SQL Database. Earlier versions require `FOR JSON PATH` or `STRING_AGG` workarounds.

---

## Question 13: MCP Server Authentication *(Easy)*

A developer configures an MCP server for Azure SQL to be used with GitHub Copilot in VS Code. Which authentication method is recommended to avoid credentials in configuration files?

A. SQL Server authentication with an encrypted password
B. Windows authentication with domain credentials
C. Active Directory Managed Identity
D. Basic authentication with Base64-encoded credentials

> [!success]- Answer
> **C. Active Directory Managed Identity**
>
> Managed Identity (`Authentication=ActiveDirectoryManagedIdentity`) allows Azure-hosted resources to authenticate without credentials in configuration. The identity is managed by Azure and automatically rotated, eliminating secret sprawl.

---

## Question 14: Columnstore — Delta Rowstore *(Hard)*

After bulk-loading 500,000 rows into a CCI table, a developer notices that some rows appear in the delta store rather than compressed column segments. What triggers compression of delta rowstore rows into column segments?

A. Running `UPDATE STATISTICS` on the table
B. The delta store reaching approximately 1,048,576 rows, triggering the tuple mover
C. Executing `DBCC CHECKDB`
D. Reaching 50% fill factor on the delta rowstore

> [!success]- Answer
> **B. The delta store reaching approximately 1,048,576 rows, triggering the tuple mover**
>
> The delta rowstore is an open B-tree rowstore that holds newly inserted rows. When it reaches ~1 million rows (one rowgroup), the background **tuple mover** compresses it into a column segment. You can also force compression immediately with `ALTER INDEX ... REORGANIZE` or `REBUILD`.

---

## Question 15: Copilot Instructions File *(Easy)*

A team wants GitHub Copilot to always follow their project's T-SQL coding standards in chat sessions. Where should these standards be defined?

A. A `copilot.config.json` file in the project root
B. `.github/copilot-instructions.md` in the repository root
C. A comment at the top of each SQL file
D. The VS Code settings.json file

> [!success]- Answer
> **B. `.github/copilot-instructions.md` in the repository root**
>
> GitHub Copilot automatically reads `.github/copilot-instructions.md` and includes it as context for all chat sessions in that repository. This is the official mechanism for project-specific instructions without requiring users to manually attach context.

---

## Question 16: FOR JSON PATH vs AUTO *(Medium)*

A developer wants full control over the JSON key names and nesting structure in the output. Which FOR JSON option should they use?

A. `FOR JSON AUTO` — automatically infers structure from the SELECT
B. `FOR JSON PATH` — uses dot-notation aliases to control nesting
C. `FOR JSON ROOT` — wraps the output in a root object
D. `FOR JSON INCLUDE_NULL_VALUES` — preserves null fields

> [!success]- Answer
> **B. `FOR JSON PATH` — uses dot-notation aliases to control nesting**
>
> `FOR JSON PATH` uses column aliases with dot notation to define the output structure: `SELECT Name AS 'product.name', Price AS 'product.price' FOR JSON PATH` creates a nested `product` object. `FOR JSON AUTO` infers nesting from table names — less predictable for complex queries.

---

## Question 17: Partitioning — Sliding Window *(Hard)*

A DBA uses a sliding window partition scheme to archive data. Each month, the oldest partition is switched to an archive table and a new empty partition is added for the next month. Which operation switches a partition to an archive table?

A. `ALTER TABLE dbo.Sales MERGE RANGE ('2024-01-01')`
B. `ALTER TABLE dbo.Sales SWITCH PARTITION 1 TO dbo.SalesArchive PARTITION 1`
C. `ALTER TABLE dbo.Sales SPLIT RANGE ('2025-01-01')`
D. `ALTER INDEX CCI_Sales REORGANIZE PARTITION = 1`

> [!success]- Answer
> **B. `ALTER TABLE dbo.Sales SWITCH PARTITION 1 TO dbo.SalesArchive PARTITION 1`**
>
> `SWITCH PARTITION` is a metadata-only operation (near-instant) that moves a partition from one table to another. Both tables must have identical structure and the target partition must be empty. `SPLIT RANGE` adds a new partition boundary; `MERGE RANGE` removes one. These three operations together implement the sliding window pattern.

---

<!-- DOMAIN 2: Secure, Optimize, Deploy (~17 questions) -->

## Question 18: Always Encrypted — Deterministic vs Randomized *(Medium)*

A developer applies Always Encrypted to a `NationalId` column. The application needs to query `WHERE NationalId = @value`. Which encryption type is required?

A. RANDOMIZED — for maximum security
B. DETERMINISTIC — to support equality comparisons
C. Either type works for equality comparisons
D. SYMMETRIC — the default Always Encrypted type

> [!success]- Answer
> **B. DETERMINISTIC — to support equality comparisons**
>
> DETERMINISTIC encryption produces the same ciphertext for the same plaintext, enabling equality comparisons (`=`, `IN`, `JOIN`) from client applications that have the column master key. RANDOMIZED encryption produces different ciphertext each time, making equality filtering impossible without Always Encrypted with Secure Enclaves.

---

## Question 19: Dynamic Data Masking — Email Function *(Easy)*

A column `EmailAddress` has `MASKED WITH (FUNCTION = 'email()')` applied. What does a user without UNMASK permission see for the value `john.doe@example.com`?

A. `XXXX`
B. `jXXX@XXXX.com`
C. `****@****`
D. `null`

> [!success]- Answer
> **B. `jXXX@XXXX.com`**
>
> The `email()` masking function shows the first character of the email prefix, replaces the rest with `XXX`, and shows the domain suffix as `XXX.com`. This format reveals just enough structure to identify it as an email without exposing the actual address.

---

## Question 20: Row-Level Security — Inline TVF *(Hard)*

An RLS security policy uses an inline table-valued function as the predicate. The function is `CREATE FUNCTION dbo.fn_rls(@RegionId int) RETURNS TABLE WITH SCHEMABINDING AS RETURN SELECT 1 AS result WHERE @RegionId IN (SELECT RegionId FROM dbo.UserRegions WHERE UserId = USER_ID())`. What does `WITH SCHEMABINDING` on the function ensure?

A. The function cannot be modified after the policy is created
B. The referenced table `dbo.UserRegions` cannot be dropped or altered without first removing the function
C. The function executes with elevated permissions
D. The function is compiled to native code for performance

> [!success]- Answer
> **B. The referenced table `dbo.UserRegions` cannot be dropped or altered without first removing the function**
>
> `WITH SCHEMABINDING` binds the function to the schema of its referenced objects. This prevents accidental schema changes (drops, column renames, type changes) to `dbo.UserRegions` that would break the RLS predicate. It is a best practice for all inline TVFs used in security policies.

---

## Question 21: GRANT/DENY/REVOKE Precedence *(Medium)*

A user `AnalystA` is a member of role `Readers` which has `SELECT GRANTED` on `dbo.FinancialData`. The DBA then runs `DENY SELECT ON dbo.FinancialData TO AnalystA`. What is the outcome?

A. The role grant takes precedence; AnalystA can SELECT
B. DENY overrides the role grant; AnalystA cannot SELECT
C. The permissions cancel out; AnalystA gets no access
D. The most recently applied permission wins; AnalystA cannot SELECT

> [!success]- Answer
> **B. DENY overrides the role grant; AnalystA cannot SELECT**
>
> SQL Server's permission model: **DENY always wins**, regardless of grants from role membership. To restore access, the DBA must `REVOKE` the explicit DENY — adding another GRANT will not help. This is a critical security principle for permission management.

---

## Question 22: Managed Identity — CREATE USER *(Medium)*

An Azure Function with a system-assigned managed identity named `MyFunction` needs read access to Azure SQL Database. What T-SQL creates the appropriate user?

A. `CREATE LOGIN [MyFunction] FROM EXTERNAL PROVIDER`
B. `CREATE USER [MyFunction] WITH PASSWORD = 'none'`
C. `CREATE USER [MyFunction] FROM EXTERNAL PROVIDER`
D. `CREATE USER [MyFunction] FOR LOGIN [MyFunction]`

> [!success]- Answer
> **C. `CREATE USER [MyFunction] FROM EXTERNAL PROVIDER`**
>
> `FROM EXTERNAL PROVIDER` creates a contained Azure AD user in the database. The name must exactly match the managed identity's display name in Azure AD. In Azure SQL Database, Azure AD identities are created as contained users directly — no server-level login is needed.

---

## Question 23: Auditing Destinations *(Easy)*

A security team requires SQL audit logs to be retained for 90 days in a queryable format for ad-hoc investigations. Which audit destination is most appropriate?

A. Azure Blob Storage
B. Azure Log Analytics workspace
C. Azure Event Hub
D. SQL Server Audit File on the local disk

> [!success]- Answer
> **B. Azure Log Analytics workspace**
>
> Log Analytics stores audit logs in queryable tables (`AzureDiagnostics`) accessible via KQL. It supports 90-day (and configurable longer) retention and enables complex security investigations. Blob Storage is durable but requires downloading files for analysis. Event Hub is for streaming/real-time processing, not ad-hoc historical queries.

---

## Question 24: RCSI — Enabling *(Easy)*

A DBA wants to enable Read Committed Snapshot Isolation for a database without requiring application code changes. Which command is correct?

A. `SET TRANSACTION ISOLATION LEVEL SNAPSHOT`
B. `ALTER DATABASE MyDB SET READ_COMMITTED_SNAPSHOT ON`
C. `ALTER DATABASE MyDB SET ALLOW_SNAPSHOT_ISOLATION ON`
D. `SET TRANSACTION ISOLATION LEVEL READ COMMITTED WITH SNAPSHOT`

> [!success]- Answer
> **B. `ALTER DATABASE MyDB SET READ_COMMITTED_SNAPSHOT ON`**
>
> RCSI is a database-level setting that changes how Read Committed isolation behaves — no application code changes needed. It automatically uses row versioning for all Read Committed transactions. `ALLOW_SNAPSHOT_ISOLATION` enables Snapshot Isolation, which requires explicit `SET TRANSACTION ISOLATION LEVEL SNAPSHOT` per session.

---

## Question 25: Deadlock — Retry Logic *(Medium)*

An application catches SQL error 1205. What is the recommended response?

A. Log the error and terminate the connection
B. Immediately retry the same transaction without delay
C. Wait for a random backoff period and retry the transaction
D. Increase the lock timeout and retry once

> [!success]- Answer
> **C. Wait for a random backoff period and retry the transaction**
>
> Error 1205 (deadlock victim) means SQL Server automatically rolled back the transaction. The application should retry after a brief delay. Using a **random backoff** (rather than a fixed delay) reduces the chance of two processes retrying simultaneously and immediately deadlocking again. Immediate retry without delay can recreate the exact same deadlock conditions.

---

## Question 26: Execution Plan — Index Seek vs Scan *(Medium)*

A query `SELECT * FROM dbo.Orders WHERE CustomerId = 42` uses an Index Scan on a non-clustered index on `CustomerId`. A developer suggests this should be an Index Seek. Under what condition would the optimizer prefer a Scan over a Seek?

A. When the index is fragmented above 30%
B. When statistics show that 42% of rows have `CustomerId = 42` (low selectivity), making a full scan cheaper
C. When the table has fewer than 1000 rows
D. When the query includes `ORDER BY`

> [!success]- Answer
> **B. When statistics show that 42% of rows have `CustomerId = 42` (low selectivity), making a full scan cheaper**
>
> The optimizer chooses Seek vs Scan based on estimated row count and selectivity. When a predicate matches a large percentage of rows, accessing rows via random I/O (Seek + Key Lookup) is more expensive than a sequential scan. The optimizer uses column statistics to estimate this. For highly selective predicates (few matching rows), Index Seek is preferred.

---

## Question 27: Missing Index DMVs *(Easy)*

A DBA wants to find the top missing indexes that could most improve query performance. Which DMV provides this information?

A. `sys.dm_exec_query_stats`
B. `sys.dm_db_missing_index_details` joined with `sys.dm_db_missing_index_group_stats`
C. `sys.dm_os_wait_stats`
D. `sys.dm_exec_cached_plans`

> [!success]- Answer
> **B. `sys.dm_db_missing_index_details` joined with `sys.dm_db_missing_index_group_stats`**
>
> The missing index DMVs track indexes that SQL Server's optimizer detected would have improved query performance. `sys.dm_db_missing_index_group_stats` provides `avg_user_impact` (estimated % improvement) and `user_seeks` + `user_scans` counts. Sort by `avg_user_impact * (user_seeks + user_scans)` to prioritize.

---

## Question 28: Query Store — Regressed Queries *(Medium)*

After a SQL Server upgrade, a business-critical query regressed from 200ms to 8 seconds. The query has not changed. What is the most likely cause and the recommended Query Store action?

A. The query text changed; rewrite the query
B. A plan regression occurred due to updated statistics or cardinality estimator changes; use Query Store to force the pre-upgrade plan
C. The table's indexes need rebuilding; run index maintenance
D. The server needs more memory; increase the buffer pool

> [!success]- Answer
> **B. A plan regression occurred due to updated statistics or cardinality estimator changes; use Query Store to force the pre-upgrade plan**
>
> Version upgrades often change the cardinality estimator (CE) version, which can cause plan regressions. Query Store's Regressed Queries report shows queries whose performance degraded and allows you to force a historically good plan with one click (`sys.sp_query_store_force_plan`).

---

## Question 29: SQL Database Projects — dacpac Deployment *(Medium)*

A team uses sqlpackage to deploy a dacpac to Azure SQL Database. Which sqlpackage action publishes the dacpac to an existing database, applying only the changes needed to bring it in sync with the model?

A. `sqlpackage /Action:Extract`
B. `sqlpackage /Action:Export`
C. `sqlpackage /Action:Publish`
D. `sqlpackage /Action:DeployReport`

> [!success]- Answer
> **C. `sqlpackage /Action:Publish`**
>
> `Publish` compares the dacpac model against the target database and generates and executes the necessary ALTER/CREATE/DROP statements to synchronize them — a declarative, idempotent deployment. `Extract` creates a dacpac from an existing database. `Export` creates a bacpac (with data). `DeployReport` generates a report of changes without applying them.

---

## Question 30: Schema Drift Detection *(Medium)*

A CI/CD pipeline deploys a dacpac to a staging database each sprint. A developer wants to detect if anyone made unauthorized schema changes directly to production (schema drift) before deploying. Which sqlpackage action should be run before deployment?

A. `sqlpackage /Action:Publish` with `/p:BlockOnPossibleDataLoss=true`
B. `sqlpackage /Action:DriftReport` against the production database
C. `sqlpackage /Action:DeployReport` comparing the dacpac to production
D. `sqlpackage /Action:Extract` to capture the current schema

> [!success]- Answer
> **C. `sqlpackage /Action:DeployReport` comparing the dacpac to production**
>
> `DeployReport` generates an XML report of all changes that *would* be made if the dacpac were published to the target — without actually deploying. If the report shows unexpected changes, it indicates schema drift. Review the report, reconcile differences, then proceed with `Publish`.

---

## Question 31: CDC vs Change Tracking — Use Case *(Hard)*

A data warehouse ETL process needs to capture all changes to `dbo.Transactions` including the **before and after values** of every UPDATE to support slowly changing dimensions. Which technology provides this?

A. Change Tracking — it captures before and after images
B. CDC (Change Data Capture) — it captures full row images in change tables
C. Temporal tables — they store current and historical rows
D. DML triggers — they can access INSERTED and DELETED pseudo-tables

> [!success]- Answer
> **B. CDC (Change Data Capture) — it captures full row images in change tables**
>
> CDC captures INSERT, UPDATE, and DELETE operations and stores both the before image (`__$operation = 3`) and after image (`__$operation = 4`) for each UPDATE in a change table. This is essential for SCD Type 2 dimensions. Change Tracking only records which rows changed (by PK), not the before values.

---

## Question 32: Azure Monitor KQL — Audit Log Query *(Medium)*

An analyst queries the Log Analytics workspace for SQL audit events. The workspace uses the `AzureDiagnostics` table. Which KQL clause filters to only SELECT statements executed in the last 24 hours?

A. `| where EventType == 'SELECT' and TimeGenerated > now() - 24h`
B. `| where Category == 'SQLSecurityAuditEvents' and statement_s startswith 'SELECT' and TimeGenerated > ago(24h)`
C. `| where OperationName == 'SELECT' and timestamp > ago(24h)`
D. `| where action_name_s == 'SELECT' and TimeGenerated > ago(24h)`

> [!success]- Answer
> **B. `| where Category == 'SQLSecurityAuditEvents' and statement_s startswith 'SELECT' and TimeGenerated > ago(24h)`**
>
> Azure SQL audit logs in `AzureDiagnostics` use `Category = 'SQLSecurityAuditEvents'`. The actual SQL statement is in `statement_s`. `TimeGenerated` is the standard Log Analytics timestamp field. `ago(24h)` returns a timestamp 24 hours before now — standard KQL time filter syntax.

---

## Question 33: DAB — REST and GraphQL *(Easy)*

A developer configures Data API Builder with a `books` entity pointing to `dbo.Books`. By default, which endpoints does DAB expose?

A. Only a REST endpoint at `/api/books`
B. Only a GraphQL endpoint at `/graphql`
C. Both a REST endpoint at `/api/books` and a GraphQL endpoint at `/graphql`
D. A WebSocket endpoint for real-time updates

> [!success]- Answer
> **C. Both a REST endpoint at `/api/books` and a GraphQL endpoint at `/graphql`**
>
> DAB automatically exposes both REST and GraphQL interfaces for each configured entity. REST follows the entity name as the path segment (`/api/books`). GraphQL uses a unified endpoint at `/graphql`. Both can be disabled per entity using `rest.enabled: false` or `graphql.enabled: false`.

---

## Question 34: Key Vault — Pipeline Secret Retrieval *(Medium)*

A pipeline needs to retrieve a secret from Azure Key Vault at deploy time. The pipeline's service principal has `Key Vault Secrets User` role. Which approach follows the principle of least privilege?

A. Grant the service principal Owner role on the Key Vault
B. Store the secret in the pipeline as a plain text variable
C. Use the `Key Vault Secrets User` role to read only the specific secrets needed
D. Grant the service principal `Key Vault Administrator` role for full access

> [!success]- Answer
> **C. Use the `Key Vault Secrets User` role to read only the specific secrets needed**
>
> `Key Vault Secrets User` (RBAC role) grants `get` and `list` on secrets only — the minimum needed for a pipeline to retrieve deployment secrets. Granting Owner or Administrator violates least privilege and would allow the pipeline to modify or delete vault contents.

---

<!-- DOMAIN 3: AI Capabilities (~11 questions) -->

## Question 35: VECTOR Data Type *(Easy)*

A table column stores embeddings from a model that outputs 768-dimensional vectors. Which column definition is correct for Azure SQL Database?

A. `Embedding float(53)`
B. `Embedding varbinary(6144)`
C. `Embedding VECTOR(768)`
D. `Embedding nvarchar(max)`

> [!success]- Answer
> **C. `Embedding VECTOR(768)`**
>
> The `VECTOR(n)` data type is native to Azure SQL Database and stores a fixed-size dense float vector of n dimensions. It enables `VECTOR_DISTANCE`, `VECTOR_SEARCH`, and `VECTOR_NORMALIZE` operations. `varbinary` and `nvarchar` are legacy workarounds that don't support native vector operations.

---

## Question 36: VECTOR_DISTANCE — Lower Is More Similar *(Easy)*

A developer runs `SELECT TOP 5 Id, VECTOR_DISTANCE('cosine', @query, Embedding) AS dist FROM dbo.Docs ORDER BY dist ASC`. What does ordering by `dist ASC` accomplish?

A. Returns the 5 least relevant documents
B. Returns the 5 most semantically similar documents (lowest distance = highest similarity)
C. Returns documents in alphabetical order
D. Has no effect since cosine distance is always 0

> [!success]- Answer
> **B. Returns the 5 most semantically similar documents (lowest distance = highest similarity)**
>
> `VECTOR_DISTANCE` returns a distance score — lower values indicate greater similarity. Ordering `ASC` and taking `TOP 5` retrieves the most similar documents. This is the standard pattern for nearest-neighbor semantic search.

---

## Question 37: ANN vs ENN — DiskANN *(Medium)*

A production vector search table has 10 million rows. A developer chooses to create a DiskANN vector index. What is the primary benefit?

A. DiskANN guarantees returning the exact mathematically nearest neighbors
B. DiskANN dramatically reduces search latency using approximate nearest neighbor (ANN) search at scale
C. DiskANN compresses vectors to reduce storage by 90%
D. DiskANN enables full-text search on vector columns

> [!success]- Answer
> **B. DiskANN dramatically reduces search latency using approximate nearest neighbor (ANN) search at scale**
>
> DiskANN is Microsoft Research's graph-based ANN index designed for billion-scale datasets. Instead of scanning all 10 million vectors, it navigates a proximity graph to find approximate nearest neighbors in milliseconds. The tradeoff is slightly reduced recall (typically >95%) versus exact search.

---

## Question 38: Chunking Strategy — Overlapping *(Medium)*

A developer chunks documents into 512-token chunks. They notice that important concepts are sometimes split across chunk boundaries, causing poor retrieval. What technique addresses this?

A. Increase the chunk size to 4096 tokens
B. Use overlapping chunks (e.g., 512 tokens with 64-token overlap between consecutive chunks)
C. Remove stop words before chunking
D. Use a smaller embedding model

> [!success]- Answer
> **B. Use overlapping chunks (e.g., 512 tokens with 64-token overlap between consecutive chunks)**
>
> Overlapping chunks ensure that context near chunk boundaries appears in multiple chunks. A concept split across the boundary of chunk N and N+1 will be fully captured within chunk N (as its tail) or chunk N+1 (as its head). Typical overlap is 10–20% of chunk size.

---

## Question 39: Embedding Maintenance — Triggers *(Hard)*

A developer uses an AFTER UPDATE trigger on `dbo.Products` to regenerate embeddings by calling `sp_invoke_external_rest_endpoint` inside the trigger body. What is the primary risk of this approach?

A. Triggers cannot call stored procedures
B. The REST call adds latency and failure risk to every UPDATE transaction, potentially causing rollbacks
C. The trigger will fire twice for each UPDATE
D. `sp_invoke_external_rest_endpoint` is not allowed in triggers

> [!success]- Answer
> **B. The REST call adds latency and failure risk to every UPDATE transaction, potentially causing rollbacks**
>
> Synchronous REST calls inside triggers extend the transaction duration (holding locks), add network latency (~100–500ms+), and if the REST endpoint fails or times out, the entire UPDATE transaction rolls back. This pattern degrades write performance and creates fragility. Preferred alternatives: Change Tracking with a background job, or Azure Functions reacting to SQL change events.

---

## Question 40: Full-Text Search — CONTAINS Syntax *(Medium)*

A developer needs to find documents containing both "machine" AND "learning" in the `Content` column. Which `CONTAINS` expression is correct?

A. `CONTAINS(Content, 'machine learning')`
B. `CONTAINS(Content, '"machine" AND "learning"')`
C. `CONTAINS(Content, 'machine & learning')`
D. `CONTAINS(Content, 'machine + learning')`

> [!success]- Answer
> **B. `CONTAINS(Content, '"machine" AND "learning"')`**
>
> `CONTAINS` uses its own search expression language where terms must be quoted and Boolean operators are keywords: `AND`, `OR`, `AND NOT`. Option A searches for the exact phrase "machine learning" (both words adjacent). Option B correctly requires both words to appear anywhere in the document.

---

## Question 41: Hybrid Search — RRF *(Hard)*

A developer combines FTS results (ranked by BM25 relevance) and vector search results (ranked by cosine distance) using Reciprocal Rank Fusion with k=60. Document A ranks 3rd in FTS and 1st in vector search. Document B ranks 1st in FTS and 5th in vector search. Which has the higher RRF score?

A. Document A — because vector search rank is more important
B. Document B — because FTS rank is more important
C. They score identically
D. Document A — `1/(60+3) + 1/(60+1) ≈ 0.0317` vs Document B — `1/(60+1) + 1/(60+5) ≈ 0.0316`; scores are nearly equal

> [!success]- Answer
> **D. Document A — `1/(60+3) + 1/(60+1) ≈ 0.0317` vs Document B — `1/(60+1) + 1/(60+5) ≈ 0.0316`; scores are nearly equal**
>
> RRF score = sum of `1/(k + rank_i)` across retrieval methods. Document A: `1/63 + 1/61 ≈ 0.01587 + 0.01639 = 0.03226`. Document B: `1/61 + 1/65 ≈ 0.01639 + 0.01538 = 0.03177`. Document A edges out slightly. This illustrates how RRF naturally balances signals from multiple retrieval methods without manual weight tuning.

---

## Question 42: RAG — sp_invoke_external_rest_endpoint *(Medium)*

A developer calls `sp_invoke_external_rest_endpoint` to query Azure OpenAI. The response is captured in `@response nvarchar(max)`. Which path correctly extracts the assistant's reply text?

A. `SELECT @response`
B. `SELECT JSON_VALUE(@response, '$.choices[0].message.content')`
C. `SELECT JSON_VALUE(@response, '$.result.choices[0].message.content')`
D. `SELECT OPENJSON(@response, '$.choices') WITH (content nvarchar(max) '$.message.content')`

> [!success]- Answer
> **C. `SELECT JSON_VALUE(@response, '$.result.choices[0].message.content')`**
>
> Common trap. `sp_invoke_external_rest_endpoint` wraps the API response under a `result` envelope: `{"response": {...}, "result": {"choices":[{"message":{"role":"assistant","content":"..."}}]}}`. Option B (`$.choices[0]...`) is the path you would use if you called Azure OpenAI directly with HttpClient — but **not** through `sp_invoke_external_rest_endpoint`. The stored procedure's `result` wrapper is the most-missed detail in T-SQL RAG implementations.

---

## Question 43: VECTORPROPERTY *(Easy)*

A developer runs `SELECT VECTORPROPERTY(EmbeddingCol, 'Dimensions') FROM dbo.Docs WHERE Id = 1` and gets `1536`. What does this confirm?

A. The column stores up to 1536 characters
B. The embedding vector for that row has 1536 dimensions
C. The table has 1536 rows
D. The embedding was generated with 1536 tokens of context

> [!success]- Answer
> **B. The embedding vector for that row has 1536 dimensions**
>
> `VECTORPROPERTY` returns metadata about a VECTOR value. `'Dimensions'` returns the number of float elements in the vector. 1536 dimensions corresponds to models like `text-embedding-ada-002`. This can be used to validate that embeddings were generated with the expected model before building a vector index.

---

## Question 44: CREATE EXTERNAL MODEL — Model Type *(Medium)*

A developer needs to register an external Azure OpenAI deployment that generates 1536-dimensional embeddings for product descriptions. Which `MODEL_TYPE` value belongs in `CREATE EXTERNAL MODEL ... WITH (...)`?

A. `MODEL_TYPE = EMBEDDINGS`
B. `MODEL_TYPE = COMPLETIONS`
C. `TASK = EMBEDDINGS`
D. `MODEL_TYPE = TEXT`

> [!success]- Answer
> **A. `MODEL_TYPE = EMBEDDINGS`**
>
> `CREATE EXTERNAL MODEL` uses the `MODEL_TYPE` keyword (not `TASK`). Valid values include `EMBEDDINGS` and `COMPLETIONS`. The `PREDICT` function uses this to shape inputs and outputs. Option C is a common confusion with model-card terminology in non-SQL platforms (LangChain, Hugging Face) where "task" is the field name — in T-SQL the keyword is `MODEL_TYPE`.

---

## Question 45: DATABASE SCOPED CREDENTIAL for REST *(Medium)*

A developer needs to create a DATABASE SCOPED CREDENTIAL to pass an Azure OpenAI API key as an HTTP header to `sp_invoke_external_rest_endpoint`. Which IDENTITY value signals that the SECRET should be injected as HTTP headers?

A. `IDENTITY = 'SHARED ACCESS SIGNATURE'`
B. `IDENTITY = 'Managed Identity'`
C. `IDENTITY = 'HTTPEndpointHeaders'`
D. `IDENTITY = 'API Key'`

> [!success]- Answer
> **C. `IDENTITY = 'HTTPEndpointHeaders'`**
>
> When `sp_invoke_external_rest_endpoint` uses a credential with `IDENTITY = 'HTTPEndpointHeaders'`, it parses the `SECRET` as a JSON object and injects each key-value pair as an HTTP request header. For Azure OpenAI: `SECRET = '{"api-key":"your-key-here"}'` results in the `api-key` header being sent with every request.

---

**[← Back to Mock Exam 1](./mock-exam-1.md)**
