---
title: "Practice Questions: Design and Develop Database Solutions"
type: practice-questions
tags:
  - dp-800
  - practice-questions
  - design-develop
---

# Practice Questions: Design and Develop Database Solutions

Domain 1 covers 35–40% of the DP-800 exam.

---

## Question 1: Column Store Index Type

**Question** *(Medium)*:

A data engineer is creating a table in Azure SQL that will be used exclusively for analytical queries aggregating hundreds of millions of rows. They want the maximum query performance for these aggregations. Which index should they create?

A. A clustered B-tree index on the date column
B. A non-clustered B-tree index on each aggregation column
C. A clustered columnstore index
D. A non-clustered columnstore index on the aggregation columns

> [!success]- Answer
> **C. A clustered columnstore index**
>
> A **clustered columnstore index (CCI)** is optimal for tables used exclusively for analytics. It:
> - Stores data by column (maximum compression)
> - Enables vectorized **batch mode execution** (~900 rows per batch)
> - Replaces the rowstore clustered index entirely
>
> Option D (non-clustered columnstore) is added alongside an existing rowstore — useful for hybrid OLTP/analytics, but not the best choice for an exclusively analytical table.

---

## Question 2: Temporal Table Query

**Question** *(Medium)*:

A developer needs to retrieve the salary value for employee ID 42 as it was on January 15, 2024. The `dbo.Employees` table is a system-versioned temporal table. Which query is correct?

A. `SELECT Salary FROM dbo.Employees WHERE EmployeeId = 42 AND ValidTo > '2024-01-15'`
B. `SELECT Salary FROM dbo.Employees FOR SYSTEM_TIME AS OF '2024-01-15' WHERE EmployeeId = 42`
C. `SELECT Salary FROM dbo.Employees FOR SYSTEM_TIME ALL WHERE EmployeeId = 42 AND '2024-01-15' BETWEEN ValidFrom AND ValidTo`
D. `SELECT Salary FROM dbo.EmployeesHistory WHERE EmployeeId = 42 AND ValidFrom <= '2024-01-15'`

> [!success]- Answer
> **B. `SELECT Salary FROM dbo.Employees FOR SYSTEM_TIME AS OF '2024-01-15' WHERE EmployeeId = 42`**
>
> `FOR SYSTEM_TIME AS OF <date>` returns the row as it existed at that exact point in time. SQL Server automatically queries both the current and history tables as needed.
>
> Option C uses `FOR SYSTEM_TIME ALL` which returns all historical rows — you'd need an additional `ORDER BY ValidFrom DESC` + `TOP 1` to get the correct row. Option D queries the history table directly but would miss the current row if it's still active.

---

## Question 3: Always Encrypted Encryption Type

**Question** *(Hard)*:

A developer is implementing Always Encrypted for a `SSN` column that must support `WHERE SSN = '123-45-6789'` filter queries from the application. Which encryption type must be used?

A. RANDOMIZED
B. DETERMINISTIC
C. SYMMETRIC
D. AES_256

> [!success]- Answer
> **B. DETERMINISTIC**
>
> With **DETERMINISTIC** encryption, the same plaintext always produces the same ciphertext — this enables equality comparisons (`=`, `IN`, `JOIN`, `GROUP BY`) from the client application.
>
> **RANDOMIZED** produces different ciphertext each time and cannot be filtered. SYMMETRIC and AES_256 are encryption algorithms, not Always Encrypted types.

---

## Question 4: JSON Function Selection

**Question** *(Easy)*:

A developer has a column `Metadata nvarchar(max)` storing JSON like `{"address":{"city":"Seattle","zip":"98101"}}`. They want to return the city value as a scalar string. Which function is correct?

A. `JSON_QUERY(Metadata, '$.address')`
B. `JSON_VALUE(Metadata, '$.address')`
C. `JSON_VALUE(Metadata, '$.address.city')`
D. `JSON_QUERY(Metadata, '$.address.city')`

> [!success]- Answer
> **C. `JSON_VALUE(Metadata, '$.address.city')`**
>
> `JSON_VALUE` returns a scalar string value from a JSON path. The path `$.address.city` correctly navigates to the nested property.
>
> Option A returns the entire `address` object as a JSON fragment (use `JSON_QUERY` for objects/arrays). Option B returns NULL because `$.address` is an object, not a scalar. Option D returns NULL because `$.address.city` is a scalar value, not an object/array.

---

## Question 5: Recursive CTE

**Question** *(Medium)*:

A developer is writing a recursive CTE to traverse an org chart. The CTE is running indefinitely and timing out. Which is the most likely cause?

A. The anchor member is returning too many rows
B. The recursive member is missing a proper termination condition causing circular references
C. The `UNION ALL` should be `UNION DISTINCT`
D. Recursive CTEs don't support `JOIN` in the recursive member

> [!success]- Answer
> **B. The recursive member is missing a proper termination condition causing circular references**
>
> Recursive CTEs must have a condition in the recursive member that eventually evaluates to FALSE (or returns no rows) to terminate. Without this, the recursion continues until the default `MAXRECURSION` limit (100) is hit — or indefinitely if the limit is raised.
>
> Common fix: Ensure a WHERE clause like `WHERE e.ManagerId IS NOT NULL` and that the data has no circular manager references. Use `OPTION (MAXRECURSION 0)` with caution — it removes the safety limit.

---

## Question 6: Window Function — Running Total

**Question** *(Medium)*:

A developer wants to calculate a running total of `TotalAmount` for each customer ordered by `OrderDate`. Which window function syntax is correct?

A. `SUM(TotalAmount) OVER (PARTITION BY CustomerId ORDER BY OrderDate)`
B. `SUM(TotalAmount) OVER (PARTITION BY CustomerId)`
C. `SUM(TotalAmount) OVER (ORDER BY OrderDate PARTITION BY CustomerId ROWS UNBOUNDED PRECEDING)`
D. `SUM(TotalAmount) GROUP BY CustomerId ORDER BY OrderDate`

> [!success]- Answer
> **A. `SUM(TotalAmount) OVER (PARTITION BY CustomerId ORDER BY OrderDate)`**
>
> This is the correct syntax for a running total: `PARTITION BY CustomerId` resets the running total per customer, and `ORDER BY OrderDate` defines the cumulative order.
>
> The default frame when `ORDER BY` is specified is `RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW`, which produces the running total. Option C has incorrect keyword order (`ROWS` must come after `ORDER BY`, not between `ORDER BY` and `PARTITION BY`).

---

## Question 7: Graph Table MATCH

**Question** *(Hard)*:

A developer has node tables `Person` and `Restaurant`, and an edge table `Likes`. They want to find all restaurants liked by friends of Alice (two-hop traversal). Which MATCH pattern is correct?

A. `MATCH(alice-(likes)->restaurant AND alice-(friendOf)->friend)`
B. `MATCH(alice-(friendOf)->friend-(likes)->restaurant)`
C. `MATCH(alice<-(friendOf)-friend-(likes)->restaurant)`
D. `MATCH(alice-(likes)->friend AND friend-(friendOf)->restaurant)`

> [!success]- Answer
> **B. `MATCH(alice-(friendOf)->friend-(likes)->restaurant)`**
>
> MATCH supports chained patterns: `node1-(edge1)->node2-(edge2)->node3` traverses two hops in a single MATCH expression. Alice → (friendOf) → friend → (likes) → restaurant correctly expresses the two-hop relationship.
>
> Option C uses reverse arrow for friendOf, which would find people who are friends with Alice (others point to Alice), not Alice's friends.

---

## Question 8: Scalar Function Performance

**Question** *(Easy)*:

A developer created a scalar UDF `dbo.fn_CalculateTax(@Amount decimal)` and uses it in a SELECT against a 50-million row table: `SELECT dbo.fn_CalculateTax(Amount) FROM dbo.Sales`. Performance is poor. What is the primary cause?

A. Scalar UDFs are not supported on large tables
B. The function lacks an index
C. Scalar UDFs execute row-by-row and prevent parallelism
D. The function needs `WITH SCHEMABINDING`

> [!success]- Answer
> **C. Scalar UDFs execute row-by-row and prevent parallelism**
>
> Scalar UDFs in T-SQL execute once per row and prevent the query optimizer from using parallel execution plans, causing severe performance degradation on large tables.
>
> **Fix**: Rewrite as an **inline table-valued function** (which can be inlined by the optimizer) or inline the expression directly in the SELECT. SQL Server 2019+ can automatically inline simple scalar UDFs.

---

## Question 9: Partitioning — RANGE Direction

**Question** *(Medium)*:

A developer creates a partition function: `CREATE PARTITION FUNCTION PF_Daily (date) AS RANGE RIGHT FOR VALUES ('2025-01-01', '2025-02-01')`. A row with value `'2025-01-01'` belongs to which partition?

A. Partition 1 (before January 2025)
B. Partition 2 (January 2025)
C. Partition 3 (February 2025 onward)
D. It depends on the partition scheme

> [!success]- Answer
> **B. Partition 2 (January 2025)**
>
> With `RANGE RIGHT`, the boundary value is the **first value in the right (newer) partition**. So `'2025-01-01'` belongs to partition 2 — the partition that starts at January 1, 2025.
>
> RANGE RIGHT means: values < `'2025-01-01'` → partition 1; values >= `'2025-01-01'` AND < `'2025-02-01'` → partition 2; values >= `'2025-02-01'` → partition 3.

---

## Question 10: Copilot Instruction Files

**Question** *(Easy)*:

A team wants GitHub Copilot to automatically use project-specific SQL conventions (like always using `datetime2` instead of `datetime`) in every chat session without manually specifying them. What should they create?

A. A `.vscode/settings.json` file with SQL preferences
B. A `.github/copilot-instructions.md` file at the repository root
C. A `CLAUDE.md` file at the repository root
D. A GitHub Actions workflow that sets Copilot context

> [!success]- Answer
> **B. A `.github/copilot-instructions.md` file at the repository root**
>
> GitHub Copilot automatically reads `.github/copilot-instructions.md` and includes its content as context in every chat session. This is the official mechanism for providing repository-specific instructions to Copilot.

---

## Question 11: Indexed View Requirements

**Question** *(Hard)*:

A developer wants to create an indexed view on `dbo.Sales` with a `GROUP BY ProductId` aggregation. Which combination of requirements must be met? (Select two)

A. The view must include `WITH SCHEMABINDING`
B. The first index must be a non-clustered unique index
C. The view must use `COUNT_BIG(*)` in the GROUP BY
D. The first index must be a unique clustered index
E. The view must use `COUNT(*)` instead of `COUNT_BIG(*)`

> [!success]- Answer
> **A and D**
>
> **A. `WITH SCHEMABINDING`** is required — prevents underlying tables from being modified.
>
> **D. Unique clustered index** — the first index on an indexed view MUST be a UNIQUE CLUSTERED index. This materializes the view.
>
> Note: `COUNT_BIG(*)` (not `COUNT(*)`) is required when GROUP BY is present — but this is a requirement for the view definition, not the index. The question asks about the required combination, so A and D are the two from the options that directly match the requirement.

---

## Question 12: JSON_ARRAYAGG Availability

**Question** *(Medium)*:

A developer wants to use `JSON_ARRAYAGG()` to aggregate product names into a JSON array per category. On which platform is this function available?

A. SQL Server 2019 and later
B. SQL Server 2016 and later
C. SQL Server 2022 and later
D. Only in Azure SQL Managed Instance

> [!success]- Answer
> **C. SQL Server 2022 and later**
>
> `JSON_ARRAYAGG` was introduced in SQL Server 2022 and Azure SQL Database. It is not available in SQL Server 2019 or earlier. On older versions, you can achieve similar results with `FOR JSON PATH` or `STRING_AGG`.

---

## Question 13: Ledger Table Properties

**Question** *(Medium)*:

A compliance team requires a table where historical records can never be deleted or modified after insertion — to serve as a tamper-evident audit trail. Which table type best meets this requirement?

A. A temporal table with `SYSTEM_VERSIONING = ON`
B. An append-only ledger table with `LEDGER = ON, APPEND_ONLY = ON`
C. An updatable ledger table with `LEDGER = ON`
D. A table with a DML trigger that prevents DELETE

> [!success]- Answer
> **B. An append-only ledger table with `LEDGER = ON, APPEND_ONLY = ON`**
>
> **Append-only ledger tables** prevent UPDATE and DELETE at the engine level — not just through triggers that could be disabled. They also maintain a cryptographic hash chain for tamper-evidence verification via `sp_verify_database_ledger`.
>
> Temporal tables track history but allow modifying and deleting current rows. DML triggers can be disabled by privileged users.

---

## Question 14: MCP Connection Authentication

**Question** *(Easy)*:

A developer is configuring an MCP server connection to Azure SQL for use with GitHub Copilot. Which authentication method is recommended for production use?

A. Username and password in the connection string
B. SQL Server authentication with a strong password
C. Active Directory Managed Identity authentication
D. Windows authentication

> [!success]- Answer
> **C. Active Directory Managed Identity authentication**
>
> Managed Identity eliminates the need for credentials in configuration files — the Azure resource authenticates using its identity from Azure AD. The connection string uses `Authentication=ActiveDirectoryManagedIdentity`.
>
> Hardcoded credentials (options A and B) risk exposure in source control or configuration files.

---

## Question 15: NOT IN vs NOT EXISTS

**Question** *(Medium)*:

A developer writes `SELECT * FROM dbo.Customers WHERE CustomerId NOT IN (SELECT CustomerId FROM dbo.Orders)`. The query returns zero rows even though there are clearly customers without orders. What is the most likely cause?

A. The subquery returns too many rows
B. There is a NULL value in the `CustomerId` column of `dbo.Orders`
C. The `CustomerId` columns have different data types
D. NOT IN cannot be used with subqueries

> [!success]- Answer
> **B. There is a NULL value in the `CustomerId` column of `dbo.Orders`**
>
> `NOT IN` returns no rows when the subquery result contains a NULL, because SQL cannot determine whether any value is "not equal to NULL" (NULL comparisons are always UNKNOWN).
>
> **Fix**: Use `NOT EXISTS` instead, which handles NULLs correctly:
> ```sql
> SELECT * FROM dbo.Customers c
> WHERE NOT EXISTS (SELECT 1 FROM dbo.Orders o WHERE o.CustomerId = c.CustomerId)
> ```

---

## Question 16: Graph — SHORTEST_PATH Edge Direction

**Question** *(Hard)*:

A developer writes a SQL graph query using `SHORTEST_PATH` to find paths between people through a `Knows` edge table. The query must follow the edge in **either direction** (A knows B implies B knows A for this traversal). Which pattern correctly expresses bidirectional traversal?

A. `MATCH (start)-(Knows+)->(end)` — single direction is sufficient because graph queries are undirected by default
B. `MATCH (start)-(Knows+)-(end)` — omit the arrow to make the edge undirected
C. `MATCH (start)-(Knows+)->(end) OR (start)<-(Knows+)-(end)` — explicit `OR` between two directed patterns
D. `MATCH SHORTEST_PATH((start)-(Knows+)->(end))` followed by a second `MATCH` for the reverse — UNION the results

> [!success]- Answer
> **D. Run two `MATCH SHORTEST_PATH` queries (one per direction) and UNION the results**
>
> SQL graph edges are **directed** — there is no built-in undirected operator. `SHORTEST_PATH` follows the declared edge direction. To traverse "either direction", define the relationship as two directional patterns and UNION them, OR store each undirected relationship as two rows in the edge table (A→B and B→A) at insert time. Option B's "omit the arrow" syntax does not exist. Option C is invalid syntax for SHORTEST_PATH (`OR` is not allowed inside the MATCH expression).
>
> **Exam trap**: candidates often assume `MATCH` is undirected like Cypher (Neo4j). SQL graph follows edge direction strictly.

---

## Question 17: Memory-Optimized Table Prerequisite

**Question** *(Hard)*:

A team wants to create memory-optimized tables in an on-premises SQL Server 2022 instance for an OLTP hot path. The first `CREATE TABLE` with `WITH (MEMORY_OPTIMIZED = ON, DURABILITY = SCHEMA_AND_DATA)` fails. Which prerequisite is most likely missing?

A. The database must be in `SIMPLE` recovery model
B. The database must have a filegroup with `CONTAINS MEMORY_OPTIMIZED_DATA`
C. The database must enable `READ_COMMITTED_SNAPSHOT`
D. The table must use the `bwin` storage engine

> [!success]- Answer
> **B. The database must have a filegroup with `CONTAINS MEMORY_OPTIMIZED_DATA`**
>
> Memory-optimized tables require a dedicated filegroup of type `MEMORY_OPTIMIZED_DATA` to persist their checkpoint files (for `DURABILITY = SCHEMA_AND_DATA`). Syntax:
>
> ```sql
> ALTER DATABASE MyDB ADD FILEGROUP MemFG CONTAINS MEMORY_OPTIMIZED_DATA;
> ALTER DATABASE MyDB ADD FILE (name='MemFile', filename='C:\Data\MemFile')
>     TO FILEGROUP MemFG;
> ```
>
> Recovery model (A) is irrelevant. RCSI (C) is unrelated. There is no "bwin storage engine" (D) — `bw-tree` is the index structure used internally but isn't named in DDL. Azure SQL Database manages this filegroup automatically — but on-prem SQL Server requires the explicit setup.

---

## Question 18: REGEXP_SPLIT_TO_TABLE

**Question** *(Medium)*:

A developer has a column `Tags nvarchar(200)` storing comma-separated values like `'azure,sql,ai,vector'`. They need to return one row per tag for joining and aggregation. Which approach uses the regex family added to Azure SQL / Fabric SQL?

A. `STRING_SPLIT(Tags, ',')` — the legacy function, fine for this case
B. `REGEXP_SPLIT_TO_TABLE(Tags, ',')` — returns one row per split element
C. `REGEXP_MATCHES(Tags, '[^,]+')` — returns a scalar count of matches
D. `REGEXP_REPLACE(Tags, ',', CHAR(10))` followed by `STRING_SPLIT`

> [!success]- Answer
> **B. `REGEXP_SPLIT_TO_TABLE(Tags, ',')` — returns one row per split element**
>
> `REGEXP_SPLIT_TO_TABLE` (added in Azure SQL Database and SQL database in Microsoft Fabric, 2025+) takes a regex separator and returns a result set with one row per split element. It is the regex-aware sibling of `STRING_SPLIT`. Both A and B would solve this specific case; the **regex family** matters when the separator is a pattern (e.g., `'[,;|]'`) rather than a single literal.
>
> `REGEXP_MATCHES` (C) is the wrong function for splitting. `REGEXP_REPLACE` (D) is convoluted. The other regex functions you should know cold for the exam: `REGEXP_LIKE`, `REGEXP_REPLACE`, `REGEXP_SUBSTR`, `REGEXP_INSTR`, `REGEXP_COUNT`, `REGEXP_MATCHES`, `REGEXP_SPLIT_TO_TABLE`.

---

**[← Back to Practice Questions](./practice-questions.md)**
