---
title: DP-800 Comparison Tables
tags:
  - dp-800
  - reference
  - comparison
---

# Comparison Tables

Quick-reference comparison tables for the DP-800 exam. Use these to solidify distinctions between commonly confused features and capabilities in Azure SQL Database.

Each table includes an exam tip callout highlighting the decision pattern most likely to appear in DP-800 questions. When reviewing, focus on the **distinguishing rows** — the features that differ between options, not the ones they share.

## Table of Contents

1. [TDE vs Always Encrypted vs Column-Level Encryption](#tde-vs-always-encrypted-vs-column-level-encryption)
2. [Clustered vs Non-Clustered vs Columnstore Indexes](#clustered-vs-non-clustered-vs-columnstore-indexes)
3. [Inline TVF vs Multi-Statement TVF](#inline-tvf-vs-multi-statement-tvf)
4. [READ COMMITTED vs RCSI vs Snapshot Isolation](#read-committed-vs-rcsi-vs-snapshot-isolation)
5. [Temporal Tables vs Ledger Tables](#temporal-tables-vs-ledger-tables)
6. [Filter Predicate vs Block Predicate (RLS)](#filter-predicate-vs-block-predicate-rls)
7. [Deterministic vs Randomized Encryption](#deterministic-vs-randomized-encryption)
8. [CONTAINS vs FREETEXT vs LIKE](#contains-vs-freetext-vs-like)
9. [ENN vs ANN Vector Search](#enn-vs-ann-vector-search)
10. [FOR JSON PATH vs FOR JSON AUTO](#for-json-path-vs-for-json-auto)
11. [Service Endpoint vs Private Endpoint](#service-endpoint-vs-private-endpoint)
12. [THROW vs RAISERROR](#throw-vs-raiserror)
13. [DAB REST vs GraphQL Endpoints](#dab-rest-vs-graphql-endpoints)
14. [ROWVERSION vs Temporal for Change Tracking](#rowversion-vs-temporal-for-change-tracking)
15. [Quick Decision Matrix](#quick-decision-matrix)

---

## TDE vs Always Encrypted vs Column-Level Encryption

SQL Server offers multiple encryption layers. The exam tests whether you can pick the right one for a given scenario based on who you are protecting against and whether the application can be modified. The three options sit at different levels of the stack: TDE encrypts at the storage layer, Always Encrypted at the client driver layer, and column-level encryption at the T-SQL function layer.

| Feature | TDE | Always Encrypted | Column Encryption (ENCRYPTBYKEY) |
|---|---|---|---|
| **Protects against** | Unauthorized access to data files on disk | Unauthorized access by DBAs and cloud operators | Unauthorized access to specific column values |
| **Encryption scope** | Entire database (all files, backups, tempdb) | Selected columns only | Selected columns only |
| **Key location** | Server (database master key in master DB) | Client-side (column master key never on server) | Server (symmetric key in database) |
| **Transparent to queries** | Yes — apps need no changes | No — requires enabled client driver | No — must call ENCRYPTBYKEY / DECRYPTBYKEY |
| **Supported query operations** | All — data decrypted in memory | Equality only (deterministic); none (randomized) | None on ciphertext directly |
| **Performance impact** | Low (page-level encrypt/decrypt) | Moderate (client-side crypto, limited query patterns) | Moderate (per-value encrypt/decrypt calls) |
| **Requires app changes** | No | Yes (driver parameter) | Yes (T-SQL function calls) |
| **Exam scenario** | Protect backups and data-at-rest with zero app changes | Protect sensitive columns from cloud admins | Encrypt specific columns with T-SQL functions |

**Key syntax:**

```sql
-- TDE: enable on database
ALTER DATABASE MyDB SET ENCRYPTION ON;

-- Always Encrypted: column definition
CREATE TABLE Patients (
    SSN NVARCHAR(11) COLLATE Latin1_General_BIN2
        ENCRYPTED WITH (ENCRYPTION_TYPE = DETERMINISTIC,
        ALGORITHM = 'AEAD_AES_256_CBC_HMAC_SHA_256',
        COLUMN_ENCRYPTION_KEY = CEK1)
);

-- Column encryption: encrypt/decrypt with symmetric key
OPEN SYMMETRIC KEY MyKey DECRYPTION BY CERTIFICATE MyCert;
SELECT CONVERT(NVARCHAR, DECRYPTBYKEY(EncryptedCol)) FROM MyTable;
```

> [!tip] Exam Tip
> If the question says "without modifying the application," the answer is TDE. If it says "protect data from database administrators," the answer is Always Encrypted.

## Clustered vs Non-Clustered vs Columnstore Indexes

Index selection is a frequent exam topic. Know the physical storage model and workload fit for each type. A single table can have one clustered index (which defines the physical row order), many non-clustered indexes, and one clustered columnstore index (which converts the entire table to columnar storage).

| Feature | Clustered | Non-Clustered | Columnstore |
|---|---|---|---|
| **Data storage** | Reorders table rows on disk (the table IS the index) | Separate B-tree structure with pointers to rows | Column-based segment storage with dictionaries |
| **Max per table** | 1 | Up to 999 | 1 clustered columnstore; multiple non-clustered columnstore |
| **Sort order** | Defines physical sort of table | Independent sort in index B-tree | N/A — segments stored by column |
| **Best for** | Range scans, primary key lookups | Selective queries, covering queries, foreign keys | Analytics, aggregations, large table scans |
| **Compression** | Row / page compression optional | Row / page compression optional | Built-in high compression (10x typical) |
| **Updateable** | Yes — standard DML | Yes — standard DML | Yes — delta store buffers updates |
| **Key size limit** | 900 bytes (16 columns) | 1700 bytes (32 columns for non-clustered) | N/A — no key concept |
| **Row vs batch mode** | Row mode execution | Row mode execution | Batch mode execution (significant perf gain) |

> [!tip] Exam Tip
> Columnstore indexes use batch mode execution by default, which is a major performance advantage for analytical queries. If the scenario involves aggregations on millions of rows, columnstore is almost always the answer.

## Inline TVF vs Multi-Statement TVF

Understanding the optimizer differences between these two function types is critical for performance tuning questions. The key insight is that inline TVFs are essentially parameterized views — the optimizer can see through them — while multi-statement TVFs are opaque black boxes that force the optimizer to guess at row counts.

| Feature | Inline TVF | Multi-Statement TVF |
|---|---|---|
| **Body structure** | Single SELECT statement (no BEGIN/END) | BEGIN/END block with INSERT into return table variable |
| **Return type** | Inferred from SELECT | Explicitly declared table variable |
| **Optimizer visibility** | Fully inlined — expanded like a view | Opaque — treated as a black box |
| **Cardinality estimation** | Accurate (based on underlying tables) | Fixed estimate (100 rows in legacy CE, 1 row in some cases) |
| **Plan caching** | Integrated into outer query plan | Separate plan; may cause poor joins |
| **Statistics** | Uses base table statistics | No statistics on table variable |
| **Performance** | Generally better — enables predicate pushdown | Generally worse — no predicate pushdown |
| **Parallelism** | Supported | Not supported (serial execution) |
| **Use when** | Parameterized view, reusable query logic | Complex procedural logic with multiple statements |

**Key syntax contrast:**

```sql
-- Inline TVF: single RETURN SELECT, no table variable
CREATE FUNCTION dbo.GetOrdersByCustomer(@CustID INT)
RETURNS TABLE
AS
RETURN (SELECT * FROM Orders WHERE CustomerID = @CustID);

-- Multi-Statement TVF: declared table variable, BEGIN/END
CREATE FUNCTION dbo.GetOrderSummary(@CustID INT)
RETURNS @Result TABLE (OrderCount INT, TotalAmount MONEY)
AS
BEGIN
    INSERT @Result
    SELECT COUNT(*), SUM(Amount) FROM Orders WHERE CustomerID = @CustID;
    RETURN;
END;
```

> [!tip] Exam Tip
> Always prefer inline TVFs over multi-statement TVFs for performance. If a question asks why a TVF performs poorly, check whether it is multi-statement — the fixed cardinality estimate is a common root cause.

## READ COMMITTED vs RCSI vs Snapshot Isolation

Isolation levels are tested heavily. Focus on blocking behavior, consistency guarantees, and how to enable each option. The key distinction is between lock-based isolation (Read Committed) and version-based isolation (RCSI and Snapshot), which use the tempdb version store to provide readers with a consistent view without acquiring shared locks.

| Feature | Read Committed | RCSI | Snapshot |
|---|---|---|---|
| **Readers block writers** | No | No | No |
| **Writers block readers** | Yes | No | No |
| **Writers block writers** | Yes | Yes | Yes (or conflict error) |
| **Consistency** | Statement-level | Statement-level | Transaction-level |
| **Version store** | Not used | tempdb version store | tempdb version store |
| **Enable method** | Default; no action needed | `ALTER DATABASE SET READ_COMMITTED_SNAPSHOT ON` | `ALTER DATABASE SET ALLOW_SNAPSHOT_ISOLATION ON` + `SET TRANSACTION ISOLATION LEVEL SNAPSHOT` |
| **Application changes** | None | None (replaces Read Committed transparently) | Yes — must set isolation level per transaction |
| **Write conflicts** | Lock-based blocking | Lock-based blocking | Error 3960 — update conflict if row changed after transaction start |
| **tempdb overhead** | None | Moderate (row versions for all updates) | Moderate (row versions for snapshot transactions) |

> [!tip] Exam Tip
> RCSI is a database-level setting that transparently replaces Read Committed behavior — no app changes needed. Snapshot isolation requires explicit `SET TRANSACTION ISOLATION LEVEL SNAPSHOT` in each transaction.

## Temporal Tables vs Ledger Tables

Both track history, but for fundamentally different reasons. Temporal is for auditing and time travel queries; ledger is for tamper-proof, cryptographically verifiable data integrity. Temporal tables let you ask "what was the value at time T?" while ledger tables let you prove "this data has not been altered since it was written."

| Feature | Temporal | Ledger |
|---|---|---|
| **Purpose** | Track data changes over time (audit, time travel) | Provide tamper-evident, cryptographically verifiable history |
| **History type** | History table with period columns | Ledger history table + database digest |
| **Tamper evidence** | No — history can be altered by DBAs | Yes — SHA-256 hash chain; external digest verification |
| **Query history** | `FOR SYSTEM_TIME AS OF / BETWEEN / FROM...TO` | Standard queries on ledger view; verification via digest |
| **DML operations** | INSERT, UPDATE, DELETE tracked automatically | INSERT, UPDATE, DELETE tracked; append-only ledger tables allow INSERT only |
| **Schema changes** | Supported (add/drop columns propagated to history) | Limited — append-only tables cannot drop columns |
| **Verification** | Compare history rows manually | `sp_verify_database_ledger` against stored digests |
| **Typical use case** | Regulatory audit trails, point-in-time reporting | Financial records, supply chain, any scenario requiring proof of integrity |

> [!tip] Exam Tip
> "Tamper-proof" or "cryptographic verification" in a question points to ledger tables. "Point-in-time query" or "AS OF" points to temporal tables.

## Filter Predicate vs Block Predicate (RLS)

Row-Level Security uses two predicate types applied via security policies. Know which direction each operates in. Both are defined as inline TVFs bound to a security policy, but they enforce access in opposite directions: filter predicates control reads while block predicates control writes.

| Feature | Filter Predicate | Block Predicate |
|---|---|---|
| **Effect** | Silently excludes rows from result sets | Raises error when violating operation is attempted |
| **Direction** | Controls what users can read | Controls what users can write |
| **When applied** | On SELECT, UPDATE (read side), DELETE (read side) | On INSERT, UPDATE (before/after), DELETE |
| **User awareness** | User does not know rows were filtered | User receives an explicit error |
| **Query impact** | Reduces result set transparently | Prevents write operations that violate policy |
| **Can be combined** | Yes — used alongside block predicates | Yes — used alongside filter predicates |
| **Common use** | Restrict row visibility per tenant or role | Prevent users from inserting/updating rows they should not own |
| **Syntax** | `ADD FILTER PREDICATE` in security policy | `ADD BLOCK PREDICATE` in security policy |

> [!tip] Exam Tip
> Filter predicates silently hide rows (reads). Block predicates raise errors on writes. A typical multi-tenant RLS policy uses both: filter to restrict reads and block to prevent cross-tenant inserts.

## Deterministic vs Randomized Encryption

Always Encrypted supports two encryption types. The choice depends on whether you need to query the encrypted column. Both use AES-256 encryption, but deterministic encryption always produces the same ciphertext for a given plaintext value, enabling equality comparisons on the server side without decryption.

| Feature | Deterministic | Randomized |
|---|---|---|
| **Same input produces same output** | Yes — identical plaintext produces identical ciphertext | No — identical plaintext produces different ciphertext each time |
| **Equality search** | Supported (`WHERE col = @param`) | Not supported |
| **Range queries** | Not supported | Not supported |
| **GROUP BY / DISTINCT** | Supported | Not supported |
| **Joins on encrypted columns** | Supported (both columns must use same key) | Not supported |
| **Security strength** | Lower — patterns can be inferred from ciphertext | Higher — no pattern leakage |
| **Use for** | Join keys, lookup columns, GROUP BY columns | Highly sensitive data where querying is not needed (e.g., SSN display only) |

> [!tip] Exam Tip
> If the scenario requires searching or joining on an encrypted column, the answer is deterministic encryption. If it emphasizes maximum security with no query requirement, choose randomized.

## CONTAINS vs FREETEXT vs LIKE

Three text search approaches with very different capabilities and performance profiles. Full-text search (CONTAINS and FREETEXT) uses an inverted index for fast linguistic matching, while LIKE performs character-by-character pattern matching. For large text columns, full-text search dramatically outperforms LIKE.

| Feature | CONTAINS | FREETEXT | LIKE |
|---|---|---|---|
| **Index required** | Full-text index | Full-text index | No (but can use B-tree index for prefix patterns) |
| **Proximity search** | Yes (`NEAR`) | No | No |
| **Inflectional forms** | Yes (`FORMSOF(INFLECTIONAL, ...)`) | Yes (automatic) | No |
| **Thesaurus support** | Yes (`FORMSOF(THESAURUS, ...)`) | Yes (automatic) | No |
| **Wildcards** | Prefix term (`"search*"`) | No | `%`, `_`, `[]` |
| **Boolean operators** | Yes (`AND`, `OR`, `AND NOT`) | No | No |
| **Performance** | Fast on large text (inverted index) | Fast on large text (inverted index) | Slow on large text (row-by-row scan unless prefix) |
| **Returns rank** | No (use CONTAINSTABLE for rank) | No (use FREETEXTTABLE for rank) | No |
| **Best for** | Precise full-text queries with Boolean logic | Natural language "find similar" queries | Simple pattern matching on short strings |

**Key syntax contrast:**

```sql
-- CONTAINS: precise full-text with Boolean and proximity
SELECT * FROM Articles
WHERE CONTAINS(Body, '"database" NEAR "performance"');

-- FREETEXT: natural language match
SELECT * FROM Articles
WHERE FREETEXT(Body, 'improving database query speed');

-- LIKE: pattern matching (only prefix is index-friendly)
SELECT * FROM Articles
WHERE Title LIKE 'Azure%';   -- can use index
-- WHERE Title LIKE '%Azure'; -- forces full scan
```

> [!tip] Exam Tip
> CONTAINS is for precise full-text searches (Boolean, proximity). FREETEXT is for fuzzy natural-language matching. LIKE is only efficient for prefix patterns (`'abc%'`); leading wildcards (`'%abc'`) force full scans.

## ENN vs ANN Vector Search

Vector search in Azure SQL Database supports both exact and approximate methods. The tradeoff is accuracy vs speed. Both use the `VECTOR_DISTANCE()` function, but ANN leverages a vector index (such as DiskANN) to avoid scanning every row. This is especially important for RAG (retrieval-augmented generation) scenarios where latency matters.

| Feature | ENN (Exact) | ANN (Approximate) |
|---|---|---|
| **Accuracy** | 100% — guaranteed nearest neighbors | High but not guaranteed — may miss true nearest |
| **Speed** | Slow on large datasets — O(n) brute-force scan | Fast — sub-linear via index |
| **Index required** | No | Yes (columnstore or DiskANN index) |
| **Function** | `VECTOR_DISTANCE()` without index hint | `VECTOR_DISTANCE()` with vector index |
| **Distance metrics** | Cosine, dot product, Euclidean | Cosine, dot product, Euclidean |
| **Scalability** | Degrades linearly with dataset size | Scales to millions/billions of vectors |
| **Recall tuning** | N/A — always 100% | Configurable via index parameters |
| **Use when** | Small datasets or exact recall required | Large-scale similarity search, RAG retrieval |

> [!tip] Exam Tip
> For RAG scenarios with large document collections, the answer is ANN with a vector index. ENN is only practical for small datasets or validation/testing scenarios.

## FOR JSON PATH vs FOR JSON AUTO

Two modes for generating JSON from query results. PATH gives you full control over the JSON shape using dot-notation aliases, while AUTO automatically creates nested structures based on the table relationships in your query. Both support `ROOT()`, `INCLUDE_NULL_VALUES`, and `WITHOUT_ARRAY_WRAPPER` options.

| Feature | PATH | AUTO |
|---|---|---|
| **Nesting control** | Full control via dot-separated column aliases | Automatic nesting based on table order in query |
| **Column aliasing** | Aliases define JSON structure (`"a.b.c"` creates nested objects) | Aliases used as property names only |
| **Output structure** | Defined explicitly by developer | Determined by FROM/JOIN clause order |
| **JOINs behavior** | Flat unless aliases create nesting | Parent-child nesting based on join relationships |
| **NULL handling** | Omits NULL by default; include with `INCLUDE_NULL_VALUES` | Omits NULL by default; include with `INCLUDE_NULL_VALUES` |
| **ROOT wrapper** | Optional (`ROOT('name')`) | Optional (`ROOT('name')`) |
| **Use when** | Specific JSON shape required, API contracts | Quick JSON output matching query structure |

**Key syntax contrast:**

```sql
-- FOR JSON PATH: dot-notation aliases control nesting
SELECT
    o.OrderID AS 'order.id',
    o.OrderDate AS 'order.date',
    c.Name AS 'order.customer.name'
FROM Orders o JOIN Customers c ON o.CustomerID = c.ID
FOR JSON PATH;

-- FOR JSON AUTO: nesting follows table relationships
SELECT o.OrderID, o.OrderDate, c.Name
FROM Orders o JOIN Customers c ON o.CustomerID = c.ID
FOR JSON AUTO;
```

> [!tip] Exam Tip
> If the question shows a specific target JSON structure with custom nesting, the answer is FOR JSON PATH. If it asks for the simplest approach to return joined data as JSON, the answer is FOR JSON AUTO.

## Service Endpoint vs Private Endpoint

Two VNet integration options for Azure SQL Database with different security and cost profiles. Service Endpoints optimize routing but keep the public endpoint, while Private Endpoints assign a private IP from your VNet, effectively bringing the service into your network.

| Feature | Service Endpoint | Private Endpoint |
|---|---|---|
| **Public IP** | Traffic stays on Azure backbone but server retains public IP | Server gets a private IP in your VNet |
| **VNet routing** | Adds optimal route to Azure service | Traffic routed entirely through private network |
| **Cross-region** | Same region only | Works across regions and even on-premises via VPN/ExpressRoute |
| **On-premises access** | Not available | Available via VPN Gateway or ExpressRoute |
| **Cost** | Free | Per-hour charge + data processing charge |
| **DNS** | No special DNS needed | Requires Private DNS Zone or custom DNS |
| **NSG support** | Yes — service tags for outbound rules | Yes — standard NSG rules on the private endpoint NIC |
| **Recommended for** | Basic VNet isolation, cost-sensitive scenarios | Production workloads, regulatory compliance, hybrid connectivity |

> [!tip] Exam Tip
> If the scenario involves on-premises connectivity or requires eliminating public IP exposure, the answer is Private Endpoint. Service Endpoints are simpler and free but only work within the same region.

## THROW vs RAISERROR

Two error-raising mechanisms in T-SQL. Modern code should prefer THROW, but RAISERROR is still valid for specific use cases. The most important distinction is that THROW can re-throw the original error in a CATCH block (parameterless `THROW;`), while RAISERROR always creates a new error message.

| Feature | THROW | RAISERROR |
|---|---|---|
| **Severity** | Always severity 16 | Configurable (0-25) |
| **Re-throw** | Yes — `THROW;` with no parameters in CATCH block | No — must specify all parameters again |
| **Terminates batch** | Yes (if not in TRY block) | Only if severity >= 20 with LOG option |
| **Error number** | Must be >= 50000 | System messages or custom (>= 50000) |
| **SET XACT_ABORT behavior** | Always respects XACT_ABORT | Only for severity >= 11 |
| **String formatting** | No — concatenate before calling | Yes — printf-style (`%s`, `%d`) |
| **Recommended** | Yes — modern best practice | Legacy — use for backward compatibility or severity control |

**Key syntax contrast:**

```sql
-- THROW: re-throw in CATCH block
BEGIN TRY
    INSERT INTO Orders VALUES (1, GETDATE());
END TRY
BEGIN CATCH
    THROW;  -- re-throws original error with original number/severity/message
END CATCH;

-- RAISERROR: must reconstruct the error
BEGIN CATCH
    DECLARE @msg NVARCHAR(2048) = ERROR_MESSAGE();
    RAISERROR(@msg, 16, 1);  -- new error, not the original
END CATCH;
```

> [!tip] Exam Tip
> `THROW;` (no parameters) in a CATCH block re-throws the original error — this is the recommended pattern. RAISERROR cannot re-throw; it creates a new error.

## DAB REST vs GraphQL Endpoints

Data API Builder (DAB) exposes both REST and GraphQL interfaces from a single configuration. Know the query patterns, URL structures, and when each is appropriate. Both are auto-generated from database objects defined in the DAB configuration file (`dab-config.json`).

| Feature | REST | GraphQL |
|---|---|---|
| **URL pattern** | `/api/<entity>` with query string filters | Single `/graphql` endpoint |
| **Query flexibility** | Fixed entity shape; filter via `$filter`, `$select`, `$orderby` | Client specifies exact fields and shape |
| **Nested data** | Separate requests per entity | Single request with nested relationships |
| **Over-fetching** | Possible — returns full entity unless `$select` used | Minimal — client requests only needed fields |
| **Mutations** | HTTP verbs: POST, PUT, PATCH, DELETE | `mutation` operations in request body |
| **Filter syntax** | OData-style (`$filter=id eq 1`) | GraphQL arguments (`filter: { id: { eq: 1 } }`) |
| **Pagination** | `$first`, `$after` for cursor-based | `first`, `after` arguments in query |
| **Best for** | Simple CRUD, standard REST clients, caching-friendly | Complex queries, mobile apps, bandwidth-sensitive scenarios |

> [!tip] Exam Tip
> DAB questions often ask you to choose between REST and GraphQL. If the scenario mentions reducing round trips or fetching related data in one call, GraphQL is the answer. If it mentions standard HTTP caching or simple CRUD, REST is the answer.

## ROWVERSION vs Temporal for Change Tracking

Both detect changes, but ROWVERSION is for optimistic concurrency while temporal tables are for full historical auditing. They solve fundamentally different problems and can be used together on the same table when you need both concurrency control and a complete audit trail.

| Feature | ROWVERSION | Temporal Table |
|---|---|---|
| **Tracks what** | Whether a row changed (binary version stamp) | Full before/after values with time range |
| **History storage** | No history — only current version number | Separate history table with all past versions |
| **Query history** | Not possible — only current value available | `FOR SYSTEM_TIME` queries for any point in time |
| **Detects concurrent change** | Yes — compare version before UPDATE | No — designed for auditing, not concurrency |
| **Column type** | `ROWVERSION` / `TIMESTAMP` (8-byte binary, auto-incremented) | `DATETIME2` period columns (SysStartTime, SysEndTime) |
| **Storage overhead** | Minimal — single 8-byte column | Moderate — full row copies to history table on every change |
| **Use case** | Optimistic concurrency control in applications | Audit trails, regulatory compliance, point-in-time recovery |
| **Combine with** | Application-level conflict detection logic | Can combine with ROWVERSION for concurrency + audit |

> [!tip] Exam Tip
> ROWVERSION answers "has this row changed since I last read it?" (concurrency). Temporal tables answer "what did this row look like at a specific point in time?" (auditing). They solve different problems and can be used together.

## Quick Decision Matrix

Use this matrix when a question describes a scenario and asks you to choose the right feature. Match the keyword or requirement to the correct answer.

| If the question mentions... | The answer is likely... |
|---|---|
| "Protect backups" or "encrypt at rest without app changes" | TDE |
| "Protect from DBA" or "client-side encryption" | Always Encrypted |
| "Encrypt specific columns with T-SQL" | Column Encryption (ENCRYPTBYKEY) |
| "Analytics on millions of rows" or "batch mode" | Columnstore index |
| "Covering query" or "included columns" | Non-clustered index |
| "Poor TVF performance" or "bad cardinality estimate" | Multi-statement TVF (replace with inline) |
| "Reduce blocking without app changes" | RCSI |
| "Transaction-level consistency" | Snapshot isolation |
| "Tamper-proof" or "cryptographic verification" | Ledger table |
| "Point-in-time query" or "AS OF" | Temporal table |
| "Silently filter rows" | Filter predicate (RLS) |
| "Prevent unauthorized inserts" | Block predicate (RLS) |
| "Search encrypted column" or "equality on encrypted data" | Deterministic encryption |
| "Maximum security, no queries needed" | Randomized encryption |
| "Proximity search" or "Boolean full-text" | CONTAINS |
| "Natural language search" | FREETEXT |
| "Millions of vectors" or "RAG retrieval" | ANN vector search |
| "Custom JSON nesting" or "dot-notation aliases" | FOR JSON PATH |
| "Eliminate public IP" or "on-premises access" | Private Endpoint |
| "Re-throw original error in CATCH" | THROW |
| "Reduce round trips" or "nested related data in one call" | GraphQL (DAB) |
| "Optimistic concurrency" or "detect concurrent changes" | ROWVERSION |
| "Full audit trail" or "regulatory compliance history" | Temporal table |

## Data Types: DECIMAL vs NUMERIC vs FLOAT

| Feature | DECIMAL(p,s) | NUMERIC(p,s) | FLOAT(n) |
|---------|-------------|-------------|---------|
| **Synonym** | Alias for NUMERIC | Alias for DECIMAL | — |
| **Precision** | Exact, user-defined | Exact, user-defined | Approximate |
| **Storage** | 5–17 bytes (by precision) | 5–17 bytes | 4 or 8 bytes |
| **Rounding** | No silent rounding | No silent rounding | Silent rounding |
| **Use for** | Money, calculations | Money, calculations | Scientific data |
| **Exam note** | DECIMAL and NUMERIC are identical | DECIMAL and NUMERIC are identical | Avoid for currency |

> **Exam tip:** DECIMAL and NUMERIC are exact synonyms in T-SQL — they behave identically. Use DECIMAL(18,2) for currency columns. Never use FLOAT for money.

## Data Types: DATETIME vs DATETIME2 vs DATE vs TIME

| Feature | DATETIME | DATETIME2(n) | DATE | TIME(n) |
|---------|----------|-------------|------|---------|
| **Date range** | 1753–9999 | 0001–9999 | 0001–9999 | N/A |
| **Accuracy** | 3.33 ms | 100 ns (default) | Day only | 100 ns |
| **Storage** | 8 bytes | 6–8 bytes | 3 bytes | 3–5 bytes |
| **ISO 8601** | No | Yes | Yes | Yes |
| **Fractional seconds** | 3 digits | 0–7 digits | None | 0–7 digits |
| **Recommended** | Legacy only | Yes — use this | Date-only values | Time-only values |

> **Exam tip:** Always prefer DATETIME2 over DATETIME for new columns — wider range, higher precision, smaller storage, and ISO-compliant. GETUTCDATE() returns DATETIME; SYSDATETIME() returns DATETIME2.

## Data Types: VARCHAR vs NVARCHAR vs CHAR vs NCHAR

| Feature | VARCHAR(n) | NVARCHAR(n) | CHAR(n) | NCHAR(n) |
|---------|-----------|------------|---------|---------|
| **Character set** | ASCII / non-Unicode | Unicode (UTF-16) | ASCII / non-Unicode | Unicode |
| **Storage** | 1 byte per char | 2 bytes per char | Fixed: n bytes | Fixed: n×2 bytes |
| **Max length** | 8,000 / MAX (2 GB) | 4,000 / MAX (2 GB) | 8,000 | 4,000 |
| **International chars** | No (depends on collation) | Yes | No | Yes |
| **Padding** | No | No | Right-padded with spaces | Right-padded with spaces |
| **Recommended** | ASCII-only, storage-sensitive | All new columns | Fixed-length codes (e.g. codes) | Fixed-length Unicode |

> **Exam tip:** Use NVARCHAR for all user-facing string columns (names, emails, descriptions) — Azure SQL databases may use non-Latin characters. CHAR/NCHAR are only appropriate for truly fixed-length data like country codes ('US', 'GB').

---

**[← Back to Appendix](./README.md)**
