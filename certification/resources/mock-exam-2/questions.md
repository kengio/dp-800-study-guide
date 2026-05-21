---
title: "DP-800 Mock Exam 2 — Questions"
type: practice-questions
tags:
  - dp-800
  - mock-exam
---

# DP-800 Mock Exam 2 — Questions

Complete all 45 questions before checking answers. Time limit: 60 minutes.

---

<!-- DOMAIN 1: Design and Develop (~17 questions) -->

## Question 1: Non-Clustered Columnstore Index *(Medium)*

A developer has an OLTP table `dbo.Sales` with a clustered B-tree index that is heavily used for INSERT/UPDATE/DELETE. The team wants to run analytical aggregations without replacing the clustered index. What is the best approach?

A. Replace the clustered B-tree index with a clustered columnstore index
B. Add a non-clustered columnstore index alongside the existing clustered index
C. Create a separate reporting database and replicate data
D. Add multiple non-clustered B-tree indexes on each aggregation column

> [!success]- Answer
> **B. Add a non-clustered columnstore index alongside the existing clustered index**
>
> A **non-clustered columnstore index (NCCI)** can coexist with a clustered B-tree index. SQL Server 2016+ made NCCIs updateable, enabling hybrid OLTP/analytics (HTAP) workloads. The clustered B-tree handles DML operations; the NCCI is used by the optimizer for analytical queries. This is often called an "HTAP" or "operational analytics" pattern.

---

## Question 2: Temporal Table — BETWEEN Syntax *(Medium)*

A developer needs all versions of a row from `dbo.Products` that were active at any point between January 1, 2025 and March 31, 2025. Which clause is correct?

A. `FOR SYSTEM_TIME AS OF '2025-01-01'`
B. `FOR SYSTEM_TIME BETWEEN '2025-01-01' AND '2025-03-31'`
C. `FOR SYSTEM_TIME FROM '2025-01-01' TO '2025-03-31'`
D. `FOR SYSTEM_TIME ALL WHERE SysStartTime >= '2025-01-01' AND SysEndTime <= '2025-03-31'`

> [!success]- Answer
> **B. `FOR SYSTEM_TIME BETWEEN '2025-01-01' AND '2025-03-31'`**
>
> `FOR SYSTEM_TIME BETWEEN start AND end` returns rows where the period overlaps the range — the row was active at any time during that window. It includes the boundary values. `FROM ... TO` is exclusive of the end date. `AS OF` returns a single point in time. Both B and C are valid syntaxes, but B uses inclusive boundaries which matches "at any point between."

---

## Question 3: OPENJSON with Schema *(Medium)*

A developer has a JSON array `[{"id":1,"name":"Alice"},{"id":2,"name":"Bob"}]` stored in a variable. They want to return it as a relational result set. Which query is correct?

A. `SELECT * FROM JSON_QUERY(@json, '$')`
B. `SELECT * FROM OPENJSON(@json) WITH (id int, name nvarchar(100))`
C. `SELECT JSON_VALUE(@json, '$[0].id'), JSON_VALUE(@json, '$[0].name')`
D. `SELECT * FROM STRING_SPLIT(@json, ',')`

> [!success]- Answer
> **B. `SELECT * FROM OPENJSON(@json) WITH (id int, name nvarchar(100))`**
>
> `OPENJSON` with the `WITH` clause (explicit schema) parses a JSON array and returns each element as a row, mapping JSON properties to typed columns. Without `WITH`, OPENJSON returns key, value, type columns for each element. This is the standard way to shred JSON arrays into relational rows.

---

## Question 4: LAG and LEAD Functions *(Easy)*

A developer wants to compare each day's sales to the previous day's sales to calculate the day-over-day change. Which function retrieves the previous row's value?

A. `LEAD(DailySales, 1) OVER (ORDER BY SaleDate)`
B. `LAG(DailySales, 1) OVER (ORDER BY SaleDate)`
C. `FIRST_VALUE(DailySales) OVER (ORDER BY SaleDate)`
D. `ROW_NUMBER() OVER (ORDER BY SaleDate) - 1`

> [!success]- Answer
> **B. `LAG(DailySales, 1) OVER (ORDER BY SaleDate)`**
>
> `LAG(column, offset)` returns the value from a row that is `offset` rows *behind* the current row in the ORDER BY sequence. `LEAD` returns a value from ahead of the current row. `LAG(DailySales, 1)` returns the previous day's value, enabling `DailySales - LAG(DailySales, 1) OVER (ORDER BY SaleDate)` for day-over-day differences.

---

## Question 5: Table Partitioning — Partition Elimination *(Hard)*

A table `dbo.Events` is partitioned by month on `EventDate`. A query filters `WHERE EventDate BETWEEN '2025-03-01' AND '2025-03-31'`. What optimization does the query plan benefit from?

A. Parallelism across all partitions simultaneously
B. Partition elimination — only the March 2025 partition is scanned
C. Automatic index creation on the EventDate column
D. Lock escalation to the partition level instead of the table level

> [!success]- Answer
> **B. Partition elimination — only the March 2025 partition is scanned**
>
> **Partition elimination** (also called partition pruning) occurs when the optimizer determines from the WHERE clause that only a subset of partitions can contain matching rows. For a date range within a single month, only that partition's data is read — dramatically reducing I/O for large partitioned tables. This is the primary performance benefit of partitioning for range queries.

---

## Question 6: Graph Tables — SHORTEST_PATH *(Hard)*

A developer wants to find the shortest path between two nodes in a graph table using SQL Server's built-in function. Which syntax is available in SQL Server 2019+?

A. `MATCH(p1-(e*)->p2)` with `SHORTEST_PATH` qualifier
B. Recursive CTE simulating BFS traversal
C. `GRAPH_PATH_SHORTEST(p1, p2, e)` function
D. `MATCH(SHORTEST_PATH(p1(-(e)->p)+p2))`

> [!success]- Answer
> **D. `MATCH(SHORTEST_PATH(p1(-(e)->p)+p2))`**
>
> SQL Server 2019 introduced `SHORTEST_PATH` inside `MATCH` for variable-length path traversal. The `+` quantifier means "one or more hops." The full pattern finds the shortest path from `p1` to `p2` through any number of edge traversals. This enables multi-hop graph queries without recursive CTEs.

---

## Question 7: Inline TVF vs Scalar UDF *(Medium)*

A developer wants to replace a slow scalar UDF with an inline table-valued function (iTVF). What is the key advantage of an iTVF?

A. iTVFs support more complex logic than scalar UDFs
B. The optimizer can inline the iTVF's query into the outer query, enabling parallelism and plan optimization
C. iTVFs return results faster because they use a cache
D. iTVFs automatically create indexes on their output

> [!success]- Answer
> **B. The optimizer can inline the iTVF's query into the outer query, enabling parallelism and plan optimization**
>
> Inline TVFs are essentially parameterized views. The optimizer substitutes the TVF's body into the calling query at compile time — it sees the complete query and can optimize it holistically, use parallelism, push predicates inside the TVF, etc. Scalar UDFs are opaque black boxes to the optimizer.

---

## Question 8: JSON_MODIFY *(Medium)*

A developer needs to update a single property inside a JSON column without replacing the entire JSON value. The column `Settings nvarchar(max)` stores `{"theme":"dark","notifications":true}`. Which function updates only the `theme` property to `"light"`?

A. `UPDATE dbo.Users SET Settings = REPLACE(Settings, 'dark', 'light')`
B. `UPDATE dbo.Users SET Settings = JSON_MODIFY(Settings, '$.theme', 'light')`
C. `UPDATE dbo.Users SET Settings = JSON_VALUE(Settings, '$.theme') + '"light"'`
D. `UPDATE dbo.Users SET Settings = JSON_QUERY(Settings, '$.theme', 'light')`

> [!success]- Answer
> **B. `UPDATE dbo.Users SET Settings = JSON_MODIFY(Settings, '$.theme', 'light')`**
>
> `JSON_MODIFY(expression, path, newValue)` returns a new JSON string with the specified path updated. It preserves all other JSON properties. `REPLACE` would break if 'dark' appeared elsewhere in the JSON. `JSON_VALUE` and `JSON_QUERY` are read-only functions.

---

## Question 9: Heap vs Clustered Table *(Easy)*

A staging table receives millions of rows via bulk insert each night, is then read in full once for transformation, and is truncated afterward. Which storage structure is most appropriate?

A. Clustered B-tree index on the surrogate key
B. Heap (no clustered index)
C. Clustered columnstore index
D. Non-clustered index on the primary key

> [!success]- Answer
> **B. Heap (no clustered index)**
>
> For bulk-insert staging tables that are always read in full and then truncated, a heap is optimal. Heaps have no index maintenance overhead during INSERT (no B-tree page splits), and `TRUNCATE TABLE` is always fast. The full-table read for transformation reads all pages anyway. If analytical aggregations were needed, a CCI would be better; for random lookup, a clustered index.

---

## Question 10: EXCEPT vs NOT IN *(Medium)*

A developer wants to find all `ProductId` values in `dbo.Products` that do not exist in `dbo.OrderItems`. Which approach correctly handles NULL values in both tables?

A. `SELECT ProductId FROM dbo.Products WHERE ProductId NOT IN (SELECT ProductId FROM dbo.OrderItems)`
B. `SELECT ProductId FROM dbo.Products EXCEPT SELECT ProductId FROM dbo.OrderItems`
C. `SELECT ProductId FROM dbo.Products p WHERE NOT EXISTS (SELECT 1 FROM dbo.OrderItems o WHERE o.ProductId = p.ProductId)`
D. Both B and C handle NULLs correctly

> [!success]- Answer
> **D. Both B and C handle NULLs correctly**
>
> `EXCEPT` treats NULLs as equal (using IS NOT DISTINCT FROM semantics) and correctly excludes products with NULL ProductId that also have a NULL in OrderItems. `NOT EXISTS` ignores NULLs in the subquery because it checks for row existence, not equality. `NOT IN` fails when the subquery returns any NULL. Both B and C are correct NULL-safe alternatives to NOT IN.

---

## Question 11: Batch Mode on Row Store *(Hard)*

A developer runs an analytical GROUP BY query on a large rowstore table without a columnstore index. SQL Server 2019 delivers much better performance than expected. What feature might explain this?

A. Automatic creation of a hidden columnstore index
B. Batch mode on rowstore — the optimizer can use batch mode execution without a columnstore index
C. Row-level compression enabled automatically
D. The query was cached from a previous columnstore execution

> [!success]- Answer
> **B. Batch mode on rowstore — the optimizer can use batch mode execution without a columnstore index**
>
> SQL Server 2019 introduced **Batch Mode on Rowstore**, allowing the optimizer to use batch mode (processing ~900 rows per CPU batch) for suitable analytical queries even without a columnstore index. This feature is enabled under database compatibility level 150 and can significantly improve complex aggregation performance on rowstore tables.

---

## Question 12: FOR JSON — WITH_WRAPPER *(Easy)*

A `FOR JSON PATH` query returns a single-element array `[{"name":"Alice"}]`. A developer wants to wrap this in a root element named `"employee"`. Which option achieves this?

A. `FOR JSON PATH, ROOT('employee')`
B. `FOR JSON AUTO, ROOT`
C. `FOR JSON PATH, INCLUDE_NULL_VALUES`
D. `FOR JSON PATH, WITHOUT_ARRAY_WRAPPER`

> [!success]- Answer
> **A. `FOR JSON PATH, ROOT('employee')`**
>
> The `ROOT('name')` option wraps the JSON array in a named root object: `{"employee":[{"name":"Alice"}]}`. `WITHOUT_ARRAY_WRAPPER` removes the outer array brackets (returns the object directly, useful for single-row results). `INCLUDE_NULL_VALUES` includes properties with null values instead of omitting them.

---

## Question 13: Columnstore — Batch Mode Operators *(Medium)*

A query against a CCI table uses batch mode. Which operators are capable of batch mode execution? (Select the best answer)

A. Only Hash Match (aggregate and join)
B. Hash Match, Bitmap Filter, Sort, Window Aggregate, and several others
C. Only Index Scan on columnstore
D. All operators automatically use batch mode on CCI tables

> [!success]- Answer
> **B. Hash Match, Bitmap Filter, Sort, Window Aggregate, and several others**
>
> Many operators have been updated to support batch mode, including: Hash Match (join and aggregate), Filter, Sort, Window Aggregate, Nested Loop (limited), Merge Join, and Compute Scalar. Not all operators support batch mode — if an unsupported operator is needed, the plan switches back to row mode. The columnstore scan itself always produces batches.

---

## Question 14: Ledger — Verification *(Medium)*

After creating an updatable ledger table and making several modifications, a compliance officer asks how to verify that the ledger's hash chain has not been tampered with. Which procedure is used?

A. `DBCC CHECKDB`
B. `sys.sp_verify_database_ledger`
C. `ALTER DATABASE ... REBUILD LEDGER`
D. `SELECT * FROM sys.database_ledger_transactions`

> [!success]- Answer
> **B. `sys.sp_verify_database_ledger`**
>
> `sys.sp_verify_database_ledger` recomputes the cryptographic hash chain for all ledger transactions and verifies it matches the stored digests. If any row has been tampered with, verification fails with an error. Digests can optionally be stored in Azure Confidential Ledger for additional trust.

---

## Question 15: PIVOT Operator *(Medium)*

A developer wants to transform rows into columns. The `dbo.SalesData` table has `(Region, Quarter, Amount)`. They want one row per Region with columns Q1, Q2, Q3, Q4. Which operator is used?

A. `UNPIVOT`
B. `PIVOT`
C. `CROSS APPLY`
D. `GROUPING SETS`

> [!success]- Answer
> **B. `PIVOT`**
>
> `PIVOT` rotates rows into columns. The basic structure is:
> ```sql
> SELECT Region, [Q1],[Q2],[Q3],[Q4]
> FROM dbo.SalesData
> PIVOT (SUM(Amount) FOR Quarter IN ([Q1],[Q2],[Q3],[Q4])) AS pvt
> ```
> `UNPIVOT` does the reverse (columns to rows). `GROUPING SETS` creates multi-level GROUP BY results without transposing.

---

## Question 16: sp_describe_first_result_set *(Easy)*

A developer wants to determine the column names and data types that a stored procedure returns without executing it. Which system procedure provides this information?

A. `sys.dm_exec_describe_first_result_set_for_object`
B. `sp_help`
C. `sys.sp_describe_first_result_set`
D. `EXEC sp_columns 'StoredProcedureName'`

> [!success]- Answer
> **C. `sys.sp_describe_first_result_set`**
>
> `sys.sp_describe_first_result_set` (or `sys.dm_exec_describe_first_result_set_for_object` for objects by ID) returns metadata about a query's or procedure's result set without executing it. This is useful for generating typed wrappers, validating output schemas, or documenting APIs.

---

## Question 17: String_Split Ordered *(Medium)*

A developer uses `STRING_SPLIT('a,b,c', ',')` and needs the results in the original order. Which additional column preserves the original position (SQL Server 2022+)?

A. `ordinal` — available when the optional third argument is `1`
B. `position` — automatically included
C. `index` — the default ordering column
D. `STRING_SPLIT` does not guarantee order; use `CHARINDEX` instead

> [!success]- Answer
> **A. `ordinal` — available when the optional third argument is `1`**
>
> SQL Server 2022 added an optional third parameter to `STRING_SPLIT`: `STRING_SPLIT(string, separator, enable_ordinal)`. When `enable_ordinal = 1`, the result set includes an `ordinal` column (1-based) indicating each element's original position. On earlier versions, `STRING_SPLIT` offers no order guarantee.

---

<!-- DOMAIN 2: Secure, Optimize, Deploy (~17 questions) -->

## Question 18: Always Encrypted — Client Driver Requirement *(Medium)*

A developer configures Always Encrypted on a `SSN` column. When they query the table using SSMS without enabling Always Encrypted in the connection, what do they see?

A. The plaintext SSN values, because SSMS has special access
B. The encrypted ciphertext bytes (unintelligible)
C. NULL for all SSN values
D. An error: "Access denied to encrypted column"

> [!success]- Answer
> **B. The encrypted ciphertext bytes (unintelligible)**
>
> Always Encrypted operates at the column level in the data — the database stores only ciphertext. Without a properly configured client (with Column Master Key access and `Column Encryption Setting=Enabled` in the connection string), any client sees raw ciphertext. Only the application with the CMK can decrypt. No error is raised — the encrypted bytes are returned as-is.

---

## Question 19: DDM — Partial Mask *(Easy)*

A `PhoneNumber` column uses `MASKED WITH (FUNCTION = 'partial(0, "XXX-XXX-", 4)')`. For stored value `425-555-1234`, what does a masked user see?

A. `XXXX`
B. `4XX-XXX-1234`
C. `XXX-XXX-1234`
D. `425-555-XXXX`

> [!success]- Answer
> **C. `XXX-XXX-1234`**
>
> The `partial(prefix_length, padding, suffix_length)` function exposes `prefix_length` characters from the start, replaces the middle with the `padding` string, and exposes `suffix_length` characters from the end. `partial(0, "XXX-XXX-", 4)` shows 0 from the start, the literal "XXX-XXX-" as padding, and 4 from the end ("1234").

---

## Question 20: RLS — BLOCK Predicate Operations *(Hard)*

An RLS security policy has a BLOCK predicate with `AFTER UPDATE`. What does `AFTER UPDATE` specifically prevent?

A. Prevents UPDATE statements from modifying any rows
B. Prevents UPDATE statements from changing a row such that it would no longer be visible to the current user
C. Prevents UPDATE statements on rows that the user cannot see
D. Prevents the user from running UPDATE at all

> [!success]- Answer
> **B. Prevents UPDATE statements from changing a row such that it would no longer be visible to the current user**
>
> `BLOCK AFTER UPDATE` checks the *new* (updated) row values against the predicate. If the update would move the row outside the user's visible range (e.g., changing the region to one the user doesn't own), the UPDATE is blocked. `BEFORE UPDATE` prevents the user from updating rows they cannot currently see. The FILTER predicate already handles preventing users from seeing rows they don't own.

---

## Question 21: Contained Database User *(Easy)*

A developer creates a user with `CREATE USER [AppUser] WITH PASSWORD = 'P@ssw0rd'`. This creates what type of user?

A. A SQL login-based user at the server level
B. A contained database user — authenticated directly by the database without a server login
C. A Windows authentication user
D. An Azure AD user

> [!success]- Answer
> **B. A contained database user — authenticated directly by the database without a server login**
>
> `CREATE USER ... WITH PASSWORD` creates a **contained database user** — their credentials are stored in the database itself, not in `sys.server_principals`. This supports database portability (the user travels with the database backup). Azure SQL Database uses contained users by default.

---

## Question 22: Snapshot Isolation — Write Conflicts *(Hard)*

Two transactions use Snapshot Isolation. Transaction 1 reads row A (value=10) and later updates it to 20. Meanwhile, Transaction 2 also read row A (value=10) under snapshot and attempts to update it to 30. What happens when Transaction 2 tries to commit?

A. Transaction 2 succeeds; the final value is 30
B. Transaction 2 gets error 3960: update conflict; it must retry
C. Transaction 2 is chosen as a deadlock victim (error 1205)
D. Transaction 2 sees Transaction 1's committed value and updates to 30 based on that

> [!success]- Answer
> **B. Transaction 2 gets error 3960: update conflict; it must retry**
>
> Snapshot Isolation detects **write-write conflicts**. When Transaction 2 attempts to update a row that was modified by another committed transaction since Transaction 2 began, SQL Server raises error 3960 (snapshot isolation transaction aborted due to update conflict). The application must handle this by retrying the transaction. This is different from RCSI, which does not detect write conflicts.

---

## Question 23: Wait Statistics Analysis *(Medium)*

A DBA observes high `PAGEIOLATCH_SH` wait counts in `sys.dm_os_wait_stats`. What is the primary cause of this wait type?

A. CPU is fully utilized and queries are waiting to execute
B. SQL Server is waiting for data pages to be read from disk into the buffer pool
C. Queries are blocked by lock contention on shared data
D. Network packets are being delayed between the client and server

> [!success]- Answer
> **B. SQL Server is waiting for data pages to be read from disk into the buffer pool**
>
> `PAGEIOLATCH_SH` (shared latch on I/O) indicates that a thread is waiting for a data page to be read from disk. High values suggest the working dataset exceeds the buffer pool (memory pressure), slow disk I/O, or excessive table/index scans causing unnecessary I/O. Remedies: add memory, optimize queries to reduce I/O, improve storage tier.

---

## Question 24: Query Hints — NOLOCK *(Medium)*

A developer adds `WITH (NOLOCK)` to a query to avoid blocking. What risk does this introduce?

A. The query will always return zero rows
B. The query may return dirty reads — uncommitted data from concurrent transactions
C. The query will acquire exclusive locks instead of shared locks
D. The query cannot use indexes

> [!success]- Answer
> **B. The query may return dirty reads — uncommitted data from concurrent transactions**
>
> `WITH (NOLOCK)` is equivalent to `READ UNCOMMITTED` isolation level — it reads data without acquiring shared locks. This means the query can read rows that are being modified by an uncommitted transaction, potentially returning data that will be rolled back. It can also return duplicate rows or miss rows during page splits. RCSI is a better alternative to avoid blocking without dirty reads.

---

## Question 25: Execution Plan — Hash Match *(Medium)*

A query joining two large tables with no useful indexes produces a Hash Match join. Which scenario would allow the optimizer to use a more efficient Merge Join instead?

A. Adding `WITH (LOOP JOIN)` hint to the query
B. Creating indexes that return both tables' rows already sorted on the join key
C. Increasing max degree of parallelism
D. Running `UPDATE STATISTICS` on both tables

> [!success]- Answer
> **B. Creating indexes that return both tables' rows already sorted on the join key**
>
> **Merge Join** requires both inputs to be sorted on the join key. If indexes (or order-preserving operations) provide pre-sorted rows on the join column, the optimizer can use Merge Join — which is highly efficient for large sorted inputs and produces results in sorted order. Hash Match is used when inputs are unsorted or when data sizes make sorting impractical.

---

## Question 26: Query Store — Automatic Plan Correction *(Hard)*

A developer configures Automatic Plan Correction (`ALTER DATABASE ... SET AUTOMATIC_TUNING (FORCE_LAST_GOOD_PLAN = ON)`). What does this feature do?

A. Rebuilds indexes automatically when fragmentation exceeds 30%
B. Detects plan regressions and automatically forces the last known good plan when a regression is confirmed
C. Automatically creates missing indexes identified by the optimizer
D. Reverts statistics to the previous version when queries degrade

> [!success]- Answer
> **B. Detects plan regressions and automatically forces the last known good plan when a regression is confirmed**
>
> When `FORCE_LAST_GOOD_PLAN` is enabled, the database engine monitors Query Store data. If a query's plan changes and performance degrades significantly, Azure SQL automatically forces the previous good plan — similar to manual Query Store plan forcing but without human intervention. It also reverts the forced plan if the new plan subsequently becomes better.

---

## Question 27: dacpac — Drift Report *(Medium)*

A DBA wants to check whether any schema changes were made directly to the production database since the last dacpac deployment. Which sqlpackage command generates this report?

A. `sqlpackage /Action:Extract /SourceConnectionString:... /TargetFile:prod.dacpac`
B. `sqlpackage /Action:DriftReport /SourceFile:baseline.dacpac /TargetConnectionString:...`
C. `sqlpackage /Action:DeployReport /SourceFile:current.dacpac /TargetConnectionString:...`
D. `sqlpackage /Action:Compare /SourceConnectionString:... /TargetFile:baseline.dacpac`

> [!success]- Answer
> **B. `sqlpackage /Action:DriftReport /SourceFile:baseline.dacpac /TargetConnectionString:...`**
>
> `DriftReport` compares a dacpac (the expected baseline) against a live database and reports changes made to the database that are not in the dacpac model. This identifies schema drift — unauthorized or undocumented changes applied directly to the database.

---

## Question 28: Auditing — Server vs Database Level *(Medium)*

An organization needs to audit all login attempts at the SQL Server instance level (across all databases) and specific DML operations only within a specific database. Which audit configuration achieves this?

A. One server audit with action groups for both logins and DML
B. A server audit for login events plus a database audit specification for DML on the specific database
C. Two database audit specifications — one for logins, one for DML
D. One server audit specification targeting both levels

> [!success]- Answer
> **B. A server audit for login events plus a database audit specification for DML on the specific database**
>
> Login events (`SUCCESSFUL_LOGIN_GROUP`, `FAILED_LOGIN_GROUP`) are server-level action groups and must be in a **server audit specification** (attached to a server-level audit). DML auditing for specific database objects is configured in a **database audit specification**. Both specifications reference the same underlying server audit (which defines the destination).

---

## Question 29: Azure AD — External Authentication *(Easy)*

A developer configures an Azure SQL Database server to use Azure Active Directory as the authentication authority. Which account type can serve as the Azure AD admin for the server?

A. Only Azure AD user accounts
B. Only Azure AD service principals
C. Azure AD users, groups, or service principals (managed identities included)
D. Only on-premises Active Directory accounts synced via AD Connect

> [!success]- Answer
> **C. Azure AD users, groups, or service principals (managed identities included)**
>
> The Azure AD admin for Azure SQL Database can be any Azure AD principal: individual user accounts, security groups, or service principals (including managed identities). Using a group is recommended — it simplifies management (add/remove group members instead of changing the admin).

---

## Question 30: Change Tracking — Sync Version *(Hard)*

A developer's application uses Change Tracking. After the first sync, the application stores a `@last_sync_version` value. On the next sync, they run `CHANGETABLE(CHANGES dbo.Orders, @last_sync_version)`. What happens if `@last_sync_version` is older than the minimum valid change tracking version (cleanup has removed older data)?

A. The function returns all rows in the table
B. The function returns no rows
C. An error is raised, signaling that the application must perform a full resync
D. The function automatically extends the retention period

> [!success]- Answer
> **C. An error is raised, signaling that the application must perform a full resync**
>
> Change Tracking has a configurable retention period. If the stored `@last_sync_version` is older than `CHANGE_TRACKING_MIN_VALID_VERSION(OBJECT_ID('dbo.Orders'))`, SQL Server raises an error (error 22122). The application must detect this, perform a full resync to re-establish a valid baseline, and store the new current version.

---

## Question 31: DAB — REST CRUD Operations *(Easy)*

By default, which HTTP methods does Data API Builder map to database operations for a REST entity?

A. GET only (read-only by default)
B. GET (read), POST (create), PUT/PATCH (update), DELETE (delete)
C. GET, POST, and DELETE only — PATCH requires explicit configuration
D. All HTTP methods are blocked until explicitly configured

> [!success]- Answer
> **B. GET (read), POST (create), PUT/PATCH (update), DELETE (delete)**
>
> DAB maps REST HTTP methods to CRUD operations: GET → read/list, POST → create (INSERT), PUT → create or replace (UPSERT), PATCH → update, DELETE → delete. Access is controlled by the `permissions` section — the `anonymous` role has no permissions by default; access must be explicitly granted.

---

## Question 32: Key Vault — Managed Identity Access *(Medium)*

An Azure SQL Database needs to retrieve a column master key from Azure Key Vault for Always Encrypted with Secure Enclaves. The database uses a system-assigned managed identity. Which role must be assigned to the managed identity on the Key Vault?

A. Key Vault Administrator
B. Key Vault Secrets User
C. Key Vault Crypto User (or Key Vault Crypto Service Encryption User)
D. Owner

> [!success]- Answer
> **C. Key Vault Crypto User (or Key Vault Crypto Service Encryption User)**
>
> Column Master Keys in Always Encrypted are **asymmetric keys** stored in Key Vault. The SQL service needs to perform cryptographic operations (key wrap/unwrap) using the CMK, which requires the **Key Vault Crypto User** role (grants `decrypt`, `encrypt`, `sign`, `verify`, `wrapKey`, `unwrapKey`). `Key Vault Secrets User` is for secrets, not keys.

---

## Question 33: Schema Drift — CI Pipeline *(Medium)*

A CI/CD pipeline should fail if a dacpac deployment to staging would require any data-loss operations (e.g., DROP TABLE, DROP COLUMN). Which sqlpackage flag achieves this?

A. `/p:AllowIncompatiblePlatform=false`
B. `/p:BlockOnPossibleDataLoss=true`
C. `/p:DropObjectsNotInSource=false`
D. `/p:IgnoreExtendedProperties=true`

> [!success]- Answer
> **B. `/p:BlockOnPossibleDataLoss=true`**
>
> `BlockOnPossibleDataLoss=true` causes sqlpackage to fail if the deployment plan includes any operation that could result in data loss (DROP TABLE, DROP COLUMN, data type change that truncates data, etc.). This is a critical safety check in CI/CD pipelines to prevent accidental destructive deployments.

---

## Question 34: sp_set_session_context Security *(Hard)*

An application uses `sp_set_session_context N'TenantId', @tenantId` with default settings. A malicious stored procedure attempts to override this value later in the same session. What prevents this?

A. Session context values are read-only once set
B. Adding `@read_only = 1` to the `sp_set_session_context` call makes the value immutable for the session
C. The value is encrypted and cannot be modified
D. Only sa can modify session context values

> [!success]- Answer
> **B. Adding `@read_only = 1` to the `sp_set_session_context` call makes the value immutable for the session**
>
> By default, session context values can be overwritten by any code executing in the same session — including malicious stored procedures or SQL injection. Setting `@read_only = 1` marks the value as immutable for the remainder of the session: `EXEC sp_set_session_context N'TenantId', @tenantId, @read_only = 1`. This is critical for security when using session context in RLS predicates.

---

<!-- DOMAIN 3: AI Capabilities (~11 questions) -->

## Question 35: External Model — Structured Output *(Medium)*

A developer uses a `CHAT_COMPLETION` external model and needs the response in a specific JSON schema for downstream processing. Which capability of modern LLM APIs supports this?

A. Prompt injection — adding "respond in JSON" to the system prompt
B. Structured output / JSON mode — configuring the model to guarantee valid JSON output matching a schema
C. Few-shot prompting with JSON examples
D. Post-processing the response with `ISJSON()` to validate

> [!success]- Answer
> **B. Structured output / JSON mode — configuring the model to guarantee valid JSON output matching a schema**
>
> Modern Azure OpenAI models support a `response_format` parameter (e.g., `{"type": "json_schema", "json_schema": {...}}`) that constrains the model's output to valid JSON matching a specified schema. This is more reliable than prompt engineering alone, which can produce malformed JSON. The schema is passed in the request payload via `sp_invoke_external_rest_endpoint`.

---

## Question 36: Vector Index — DiskANN with the `dot` Metric *(Hard)*

A developer creates a DiskANN vector index with `METRIC = 'dot'` and wants the results to behave like cosine similarity. Which prerequisite must be met?

A. The column must be the primary key
B. The vectors must be normalized to unit length (apply `VECTOR_NORMALIZE` before inserting)
C. The table must have fewer than 1 million rows
D. The column must use `VECTOR(512)` or smaller dimensions

> [!success]- Answer
> **B. The vectors must be normalized to unit length (apply `VECTOR_NORMALIZE` before inserting)**
>
> Dot product equals cosine similarity only when both vectors have unit magnitude. To use `dot` as a faster proxy for cosine, normalize stored vectors with `VECTOR_NORMALIZE(..., 'norm2')` before insert/update. **Note: `cosine` itself does NOT require pre-normalization** — the cosine metric handles magnitudes internally. The "normalize before indexing" rule is specific to the `dot` metric being used as a cosine proxy.

---

## Question 37: Full-Text Index — FREETEXTTABLE *(Medium)*

A developer uses `FREETEXTTABLE(dbo.Docs, Content, 'database performance tuning')` and joins the result. What does this function return compared to `FREETEXT`?

A. The same rows as `FREETEXT` but without NULL values
B. A table with `KEY` and `RANK` columns, enabling results to be sorted by relevance
C. Only the top 10 results by default
D. A comma-separated list of matching document IDs

> [!success]- Answer
> **B. A table with `KEY` and `RANK` columns, enabling results to be sorted by relevance**
>
> `FREETEXTTABLE` is the rowset-valued version of `FREETEXT`. It returns a table with `KEY` (the full-text key value, e.g., the primary key) and `RANK` (relevance score 0–1000). This enables ranked retrieval: join on `KEY`, order by `RANK DESC` to surface the most relevant documents first.

---

## Question 38: Chunking — Semantic Chunking *(Hard)*

A developer implements semantic chunking for a technical manual. Instead of splitting by token count, they split at paragraph boundaries and then merge small paragraphs until reaching a target size. What is the primary advantage of this approach over fixed-size chunking?

A. Semantic chunking always produces smaller chunks
B. Each chunk contains a semantically coherent unit, improving the embedding's representativeness
C. Semantic chunking is faster to compute
D. Semantic chunking works with any language model

> [!success]- Answer
> **B. Each chunk contains a semantically coherent unit, improving the embedding's representativeness**
>
> When a chunk corresponds to a complete thought or topic (a paragraph or section), the embedding more accurately captures the chunk's meaning. Fixed-size chunks often split mid-sentence or mid-idea, producing embeddings that mix two topics — making them harder to retrieve accurately. The tradeoff is more complex chunking logic and variable chunk sizes.

---

## Question 39: VECTOR_SEARCH — Current Syntax *(Medium)*

A developer wants the 10 most similar products to a query embedding against a **latest-version** DiskANN vector index on Azure SQL. Which clause is the recommended current syntax?

A. `SELECT TOP (10) ... ORDER BY VECTOR_DISTANCE('cosine', col, @q) WITH APPROXIMATE`
B. `WITH (TOP_K = 10)` in the VECTOR_SEARCH options
C. `LIMIT 10` at the end of the query
D. `VECTOR_SEARCH(..., TOP_N = 10)`

> [!success]- Answer
> **A. `SELECT TOP (10) ... ORDER BY VECTOR_DISTANCE('cosine', col, @q) WITH APPROXIMATE`**
>
> On latest-version vector indexes, the current pattern is `SELECT TOP (N) ... ORDER BY VECTOR_DISTANCE(...) WITH APPROXIMATE`. The legacy `VECTOR_SEARCH(... TOP_N = n)` table-valued form is **deprecated** on current indexes — passing `TOP_N` raises Msg 42274. `TOP_K` (option B) is not a real parameter name. `LIMIT` is not T-SQL syntax. To raise recall, increase `N` in `TOP (N)`.

---

## Question 40: RAG — FOR JSON in REST Payload *(Medium)*

A developer builds a RAG prompt by concatenating retrieved chunks into a T-SQL string and passing it to `sp_invoke_external_rest_endpoint`. The chunks contain special characters (quotes, backslashes). What is the safest way to build the JSON payload?

A. Use `REPLACE(@context, '"', '\"')` to escape quotes before concatenation
B. Use `JSON_OBJECT` and `JSON_ARRAY` to construct the payload — these functions handle escaping automatically
C. Use `CAST(@context AS nvarchar(max))` to sanitize the string
D. Use `STRING_ESCAPE(@context, 'json')` before embedding in the string

> [!success]- Answer
> **B. Use `JSON_OBJECT` and `JSON_ARRAY` to construct the payload — these functions handle escaping automatically**
>
> `JSON_OBJECT` and `JSON_ARRAY` (SQL Server 2022+) automatically escape special characters in their inputs, producing valid JSON without manual escaping. `STRING_ESCAPE(@context, 'json')` (option D) is also valid for SQL Server 2016+ when you need to embed a string value safely — but using `JSON_OBJECT` for the whole structure is cleaner and less error-prone.

---

## Question 41: Hybrid Search — Implementation *(Hard)*

A developer implements hybrid search combining FTS (`CONTAINSTABLE`) and vector search. After getting separate ranked lists, they apply RRF with k=60. The final result should return the top 5 documents. Which CTE structure correctly implements this?

A. Union the two result sets and take TOP 5 by the highest individual RANK
B. Compute RRF scores by summing `1/(60+rank)` from each result set per document, then order by RRF score descending and take TOP 5
C. Multiply the FTS RANK by the vector distance and take the minimum 5
D. Take TOP 5 from FTS and TOP 5 from vector search, then union and deduplicate

> [!success]- Answer
> **B. Compute RRF scores by summing `1/(60+rank)` from each result set per document, then order by RRF score descending and take TOP 5**
>
> RRF formula: for each document, `RRF_score = Σ 1/(k + rank_i)` across all retrieval systems where `rank_i` is the document's rank in system `i`. Documents appearing in multiple systems accumulate higher scores. Sort descending by RRF score and take TOP 5. This avoids the problems of incomparable raw scores (BM25 vs. cosine distance) and requires no normalization.

---

## Question 42: Embedding Model — Dimensions Trade-off *(Medium)*

A team is choosing between `text-embedding-3-small` (1536 dims) and `text-embedding-3-large` (3072 dims). They have 50 million documents and cost/storage is a concern. What is the key trade-off?

A. Larger dimensions always produce worse results for non-English text
B. Larger dimensions generally produce higher quality embeddings at the cost of more storage, higher compute, and slower vector search
C. Smaller dimensions cannot be used with VECTOR_SEARCH
D. The dimension count has no practical impact on retrieval quality

> [!success]- Answer
> **B. Larger dimensions generally produce higher quality embeddings at the cost of more storage, higher compute, and slower vector search**
>
> Higher-dimensional embeddings capture more semantic nuance and typically score better on retrieval benchmarks. However, with 50 million documents: 1536 dims ≈ 300GB storage; 3072 dims ≈ 600GB. ANN search also slows with higher dimensions. Modern models like `text-embedding-3` support Matryoshka Representation Learning — you can truncate to fewer dimensions (e.g., 512) with modest quality loss for large-scale applications.

---

## Question 43: sp_invoke_external_rest_endpoint — Response Status *(Easy)*

After calling `sp_invoke_external_rest_endpoint`, the output parameters include `@response_headers` and `@status_code`. What HTTP status code indicates a successful Azure OpenAI response?

A. 201
B. 204
C. 200
D. 202

> [!success]- Answer
> **C. 200**
>
> Azure OpenAI (and most REST APIs) return HTTP 200 OK for successful synchronous requests. The response body (accessible via the procedure's result set or output variable) contains the JSON response. Applications should always check `@status_code` before processing the response — non-200 codes (429 = rate limit, 400 = bad request, 500 = server error) require different handling.

---

## Question 44: CREATE EXTERNAL MODEL — Credential *(Medium)*

A developer creates a DATABASE SCOPED CREDENTIAL for an Azure OpenAI model using Managed Identity rather than an API key. Which IDENTITY value is used?

A. `IDENTITY = 'HTTPEndpointHeaders'`
B. `IDENTITY = 'Managed Identity'`
C. `IDENTITY = 'SHARED ACCESS SIGNATURE'`
D. `IDENTITY = 'Azure Active Directory'`

> [!success]- Answer
> **B. `IDENTITY = 'Managed Identity'`**
>
> When the Azure SQL Database server's managed identity has been granted the **Cognitive Services OpenAI User** role on the Azure OpenAI resource, you create the credential with `IDENTITY = 'Managed Identity'` and no SECRET. The database engine acquires a token using the server's managed identity automatically — no API key required.

---

## Question 45: Vector Search — Combining with WHERE Filter *(Hard)*

A developer runs a `VECTOR_SEARCH` query but needs to restrict results to documents where `Category = 'Finance'`. The `Category` column has a regular B-tree index. What is the most efficient approach?

A. Run `VECTOR_SEARCH` first, return all results, then filter in the application layer
B. Add a `WHERE Category = 'Finance'` filter in the outer query that joins to the `VECTOR_SEARCH` result — the optimizer applies the filter post-ANN
C. Create a filtered DiskANN index on the subset of Finance documents
D. Use `CONTAINS(Category, 'Finance')` inside the VECTOR_SEARCH call

> [!success]- Answer
> **B. Add a `WHERE Category = 'Finance'` filter in the outer query that joins to the `VECTOR_SEARCH` result — the optimizer applies the filter post-ANN**
>
> The current pattern for pre-filtering with vector search is to apply the scalar filter in the outer query after `VECTOR_SEARCH` retrieves ANN candidates. Set `TOP_K` higher than the final desired result count to account for post-filter reduction. Filtered vector indexes (option C) are a more advanced capability available in some vector databases but the post-filter approach is the standard pattern in Azure SQL Database today.

---

## Case Study: Northwind RAG Product Catalog *(5 linked questions, ~10 minutes)*

> [!info] Case-study format
> The real DP-800 includes interactive case studies — a multi-paragraph scenario followed by linked questions. Read the whole scenario once, then answer Q46–Q50 in order. You can navigate within the case study, but cannot return to it after submission.

**Scenario**

Northwind is building a semantic product-catalog search and Q&A assistant on **Azure SQL Database**. Requirements:

1. **Catalog**: ~2 million products with `Description nvarchar(max)` (typically 200–1 200 words per product) and a separate `Specifications nvarchar(max)` JSON block with structured attributes.
2. **Embedding model**: `text-embedding-3-small` (1536 dims) is chosen for cost. Embeddings must stay synchronised whenever `Description` changes — but **write throughput is high (~5 000 updates/min)** and the embedding API must not block writes.
3. **Search**: customers' natural-language queries should return relevant products even when the query phrasing doesn't match the product description verbatim. The team also wants exact keyword matches ("waterproof", "Wi-Fi 7") to rank well.
4. **Q&A**: a follow-up assistant generates a 1–2 sentence answer grounded on the top-K retrieved product chunks.
5. **Production scale**: search latency target is p95 < 200 ms across 2 M products.

---

### Question 46: Chunking strategy *(Medium)*

Product descriptions vary from 200 to 1 200 words. Many products have multi-paragraph descriptions covering specs, materials, and warranty separately. Which chunking strategy fits best?

A. One chunk per product (embed the entire `Description`)
B. Fixed-size 200-token chunks with 10–20 % overlap
C. **Paragraph-based chunking with 10–20 % overlap** between adjacent chunks
D. One chunk per character (max granularity)

> [!success]- Answer
> **C. Paragraph-based chunking with 10–20 % overlap**
>
> Paragraph-based chunking preserves semantic units (specs paragraph vs warranty paragraph) so each embedding represents one coherent thought. Overlap prevents losing a sentence that straddles a paragraph boundary. Option A buries detail (a 1 200-word embedding averages too many topics). Fixed-size chunking can split mid-sentence, degrading retrieval. Single-character chunking is meaningless.

---

### Question 47: Embedding maintenance for high write volume *(Hard)*

With 5 000 updates/min, the team must keep embeddings fresh without blocking writes. Which approach is best suited?

A. A synchronous `AFTER UPDATE` trigger calling `PREDICT` inline
B. **Change Tracking** with a background job (Azure Functions SQL trigger binding or SQL Agent) that re-embeds changed rows in batches
C. CDC with a custom .NET consumer
D. Azure Logic Apps polling every 5 minutes

> [!success]- Answer
> **B. Change Tracking with a background job (Azure Functions SQL trigger binding) that re-embeds changed rows in batches**
>
> Synchronous triggers (A) would add embedding-API latency to every write and timeout under load. Change Tracking is lightweight — captures only the changed row's PK — and the Azure Functions SQL trigger uses CT internally. Batching across multiple rows per invocation amortises the API cost. CDC works but is heavier than needed when you only need to know *which* rows changed (you can read current values from the table). Logic Apps' 5-minute cadence is too slow.

---

### Question 48: Vector index choice and metric *(Medium)*

For the 2 M-row catalog with p95 < 200 ms latency, which index and metric should be configured?

A. No index — use `VECTOR_DISTANCE` in `ORDER BY` (exact kNN)
B. **DiskANN vector index with `METRIC = 'cosine'`**, and queries use `SELECT TOP (N) ... WITH APPROXIMATE` with cosine
C. DiskANN with `METRIC = 'dot'`, no normalisation
D. A traditional B-tree index on the `DescriptionEmbedding` column

> [!success]- Answer
> **B. DiskANN with `METRIC = 'cosine'`, queries use `SELECT TOP (N) ... WITH APPROXIMATE` with cosine**
>
> Exact kNN (A) scans every row — p95 > 200 ms at 2 M rows. DiskANN with `cosine` is the standard choice for text embeddings (magnitude-invariant). The query metric must match the index metric — mismatch logs a warning and silently falls back to exact kNN (perf trap). `dot` (C) needs pre-normalisation to behave like cosine; pick one or the other. B-tree (D) cannot index float arrays.

---

### Question 49: Hybrid search with RRF *(Hard)*

Customers want both semantic relevance AND exact keyword matches to rank well ("waterproof", "Wi-Fi 7"). How should the team combine signals?

A. Run vector search only — semantic embeddings capture keyword meaning
B. Run full-text `CONTAINS` only — keyword matching is exact
C. **Run both: vector search (cosine) AND full-text (`CONTAINSTABLE` for RANK), then combine via Reciprocal Rank Fusion (`score = Σ 1/(60 + rank_i)`)**
D. Run vector search, then run `LIKE '%keyword%'` on the results

> [!success]- Answer
> **C. Run both vector and full-text, combine via Reciprocal Rank Fusion**
>
> RRF is the standard hybrid retrieval pattern: each method ranks documents independently, then ranks (not raw scores — which have different scales) are fused with `1/(k+rank)` where `k=60` is the common default. Higher combined score wins. Pure vector (A) can miss exact terms; pure FTS (B) misses semantic paraphrases; `LIKE` (D) cannot use the full-text index and won't rank well.

---

### Question 50: Q&A grounding and prompt-shape *(Medium)*

The Q&A assistant must answer using only the retrieved chunks. Which combination of model-call settings best minimises hallucination?

A. System prompt: "answer creatively"; temperature 0.9; pass query only
B. System prompt: "answer using only the provided product excerpts; if not present, say so"; **temperature 0.1**; pass retrieved chunks as a system message; parse with `JSON_VALUE(@resp, '$.result.choices[0].message.content')`
C. Temperature 0.5; pass the user query but not the retrieved chunks
D. Use `JSON_VALUE(@resp, '$.choices[0].message.content')` and a high temperature

> [!success]- Answer
> **B. System message constrains to provided excerpts; temperature 0.1; chunks passed as system message; parse with `$.result.choices[0].message.content`**
>
> Low temperature reduces creative drift for grounded Q&A. The system message must say "use only the excerpts" — otherwise the model fills gaps from training data. **`sp_invoke_external_rest_endpoint` wraps the API response under `$.result`** (not `$.choices[0]` as you'd get calling Azure OpenAI directly) — option D's path is the single most-missed RAG detail. Without retrieved chunks (A, C), the model has nothing to ground on.

---

**[← Back to Mock Exam 2](./mock-exam-2.md)**
