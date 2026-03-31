---
title: DP-800 Glossary
tags:
  - dp-800
  - glossary
  - reference
---

# DP-800 Glossary

A reference of key terms and concepts for the DP-800: Developing AI-Enabled Database Solutions exam.

---

## A

| Term | Definition |
|------|-----------|
| **Always Encrypted** | A SQL Server/Azure SQL feature that encrypts sensitive column data on the client side, ensuring the database engine never sees plaintext values. Supports Deterministic and Randomized encryption modes. |
| **ANN (Approximate Nearest Neighbor)** | A search algorithm that finds vectors close to a query vector without scanning every row, trading perfect accuracy for significantly faster retrieval. Used in vector search scenarios. |
| **APPLY (CROSS/OUTER)** | A T-SQL operator that invokes a table-valued function or subquery for each row of the outer table. CROSS APPLY returns only matching rows; OUTER APPLY includes rows with no match (NULLs for unmatched columns). |

---

## B

| Term | Definition |
|------|-----------|
| **Block Predicate (RLS)** | A Row-Level Security predicate that prevents INSERT, UPDATE, or DELETE operations when the predicate function returns false, controlling which rows a user can write. |

---

## C

| Term | Definition |
|------|-----------|
| **CDC (Change Data Capture)** | A SQL Server feature that records INSERT, UPDATE, and DELETE activity on tables into change tables, enabling downstream systems to track and consume data changes incrementally. |
| **CEK (Column Encryption Key)** | The symmetric key used by Always Encrypted to encrypt individual column values. A CEK is itself encrypted by a Column Master Key stored outside the database. |
| **Chunking** | The process of splitting large documents or text into smaller overlapping or non-overlapping segments before generating embeddings, enabling more precise vector search in RAG pipelines. |
| **CMK (Column Master Key)** | The root key in the Always Encrypted key hierarchy, stored in a trusted external key store (e.g., Azure Key Vault or Windows Certificate Store) and used to encrypt Column Encryption Keys. |
| **Columnstore Index** | A storage format that organizes data by column rather than row, enabling high-compression and batch-mode execution for analytic workloads. Available as clustered or non-clustered. |
| **Containment** | A database property that limits cross-database dependencies. A contained database stores authentication and collation settings internally, reducing reliance on the master database. |
| **CONTAINSTABLE** | A full-text search function that returns a table with a RANK column indicating relevance for rows matching complex full-text predicates, used in the FROM clause with CROSS APPLY. |
| **Cosine Distance** | A vector similarity metric measuring the angle between two vectors regardless of magnitude. A cosine distance of 0 means identical direction; commonly used for text embedding similarity. |
| **CROSS APPLY** | See APPLY. Returns only rows from the outer table for which the applied expression produces at least one row. |
| **CTE (Common Table Expression)** | A named temporary result set defined with the `WITH` clause that can be referenced once in the immediately following SELECT, INSERT, UPDATE, DELETE, or MERGE statement. Supports recursion. |

---

## D

| Term | Definition |
|------|-----------|
| **DAB (Data API Builder)** | An open-source tool from Microsoft that automatically generates REST and GraphQL APIs over Azure SQL, SQL Server, and other data sources without custom application code. |
| **Database Scoped Credential** | A credential stored within a specific database (not server-wide) that provides authentication details for accessing external resources such as Azure Blob Storage or external REST endpoints. |
| **DDL Trigger** | A trigger that fires in response to DDL events such as CREATE, ALTER, or DROP statements, used for auditing schema changes or preventing unauthorized modifications. |
| **Deadlock** | A situation where two or more sessions each hold a lock that the other needs, causing all sessions involved to wait indefinitely. SQL Server automatically detects and resolves deadlocks by terminating one session as a victim. |
| **Deterministic Encryption** | An Always Encrypted mode that always produces the same ciphertext for a given plaintext value, enabling equality lookups and joins on encrypted columns. Less secure than Randomized encryption. |
| **DiskANN** | A graph-based approximate nearest neighbor indexing algorithm used by Azure SQL Database for efficient vector search at scale, balancing high recall with low query latency. |
| **DMV (Dynamic Management View)** | A system view in SQL Server prefixed with `sys.dm_` that exposes internal server state, health, and performance metrics useful for monitoring and troubleshooting. |
| **Dot Product Distance** | A vector similarity metric computed as the sum of element-wise products. Higher values indicate greater similarity; valid for comparing normalized vectors where it is equivalent to cosine similarity. |
| **Dynamic Data Masking** | A feature that obfuscates sensitive column data in query results for unauthorized users without changing the stored data. Masking rules are defined at the column level and applied at query time. |

---

## E

| Term | Definition |
|------|-----------|
| **Edge (Graph)** | A table in a SQL graph database that represents a relationship between two node tables, storing `$from_id` and `$to_id` columns that reference node rows. |
| **Embedding** | A fixed-length numeric vector that represents the semantic meaning of text, images, or other data, produced by a machine learning model and stored for use in similarity search. |
| **ENN (Exact Nearest Neighbor)** | A vector search method that computes the distance from the query vector to every stored vector and returns the true nearest neighbors. Accurate but does not scale to large datasets. |
| **Euclidean Distance** | A vector distance metric measuring the straight-line distance between two points in vector space. Smaller values indicate greater similarity; sensitive to vector magnitude. |
| **EXECUTE AS** | A T-SQL clause that changes the security context in which a module (stored procedure, function, trigger) executes, enabling ownership chaining and privilege delegation. |
| **Execution Plan** | A graphical or XML representation of the steps SQL Server's query optimizer chooses to execute a query, showing operators, estimated costs, row counts, and data flow. |
| **Extended Events** | A lightweight performance monitoring framework in SQL Server that captures server events with minimal overhead, replacing SQL Trace and Profiler for production diagnostics. |
| **External Model** | An AI or ML model hosted outside the database (e.g., in Azure OpenAI) that is registered in Azure SQL via `sp_configure` or system objects, enabling the database to invoke it for inference. |

---

## F

| Term | Definition |
|------|-----------|
| **Filtered Index** | A non-clustered index with a WHERE clause that indexes only a subset of rows, reducing index size and maintenance overhead while improving query performance for selective predicates. |
| **Filter Predicate (RLS)** | A Row-Level Security predicate applied to SELECT, UPDATE, and DELETE operations that silently filters rows the current user is not authorized to see. |
| **FOR JSON** | A T-SQL clause appended to a SELECT statement that serializes result set rows as a JSON array or object. Supports AUTO, PATH, and ROOT options for controlling output structure. |
| **FREETEXT** | A full-text search predicate that matches rows containing words or phrases semantically similar to the search term, using word-breaking, stemming, and thesaurus expansion automatically. |
| **Full-Text Search** | A SQL Server feature that creates inverted indexes (full-text indexes) over character-based columns, enabling linguistic searches with CONTAINS, FREETEXT, CONTAINSTABLE, and FREETEXTTABLE. |

---

## G

| Term | Definition |
|------|-----------|
| **GitHub Copilot** | An AI-powered coding assistant integrated into IDEs and GitHub that generates, explains, and refactors code using large language models, including T-SQL suggestions in VS Code and SSMS. |
| **Graph Table** | A node or edge table in SQL Server's graph database feature, identified by `AS NODE` or `AS EDGE` in the CREATE TABLE statement, enabling graph pattern matching with the MATCH clause. |
| **Grounding** | The process of providing an AI model with factual, retrieved context (e.g., database query results) so its generated responses are based on accurate, current data rather than parametric knowledge alone. |

---

## H

| Term | Definition |
|------|-----------|
| **Hybrid Search** | A retrieval strategy that combines full-text (keyword) search and vector (semantic) search results, typically merged using Reciprocal Rank Fusion (RRF) to leverage both lexical precision and semantic recall. |

---

## I

| Term | Definition |
|------|-----------|
| **Included Columns** | Non-key columns added to a non-clustered index using the INCLUDE clause, stored only at the leaf level of the index to satisfy covering queries without increasing the index key size. |
| **Indexed View** | A view whose result set has been materialized and stored on disk with a unique clustered index, enabling faster query execution for aggregations and joins at the cost of additional storage and write overhead. |
| **Inline TVF** | An inline table-valued function defined as a single SELECT statement, processed by the optimizer as a parameterized view and inlined into the calling query for efficient execution. |

---

## J

| Term | Definition |
|------|-----------|
| **JSON_ARRAYAGG** | A T-SQL aggregate function (SQL Server 2022+) that collects values from multiple rows into a JSON array, similar to STRING_AGG but producing valid JSON output. |
| **JSON_OBJECTAGG** | A T-SQL aggregate function (SQL Server 2022+) that builds a JSON object from key-value pairs across multiple rows within a group. |
| **JSON_VALUE** | A T-SQL function that extracts a scalar value from a JSON string using a JSON path expression, returning NULL if the path does not exist or the value is not scalar. |
| **JSON_QUERY** | A T-SQL function that extracts a JSON object or array fragment from a JSON string using a JSON path expression, returning NULL for scalar values. |

---

## K

| Term | Definition |
|------|-----------|
| **Key Lookup** | An execution plan operator that retrieves additional columns from the clustered index (or heap) for rows identified by a non-clustered index seek, indicating the index does not cover the query fully. |

---

## L

| Term | Definition |
|------|-----------|
| **Ledger Table** | An Azure SQL or SQL Server 2022 table type that provides cryptographically verified tamper-evident history, recording all changes in an append-only ledger and enabling auditability without trusting database administrators. |
| **Lock Escalation** | The process by which SQL Server converts many fine-grained row or page locks into a single table lock to reduce memory overhead, which can increase blocking and reduce concurrency. |

---

## M

| Term | Definition |
|------|-----------|
| **Managed Identity** | An Azure Active Directory identity automatically managed by Azure for a resource (e.g., Azure SQL, App Service), allowing passwordless authentication to other Azure services without storing credentials. |
| **MATCH** | A T-SQL clause used in graph queries within the WHERE clause to specify graph pattern matching expressions across node and edge tables, supporting path traversal and relationship filters. |
| **MAXDOP** | A query hint and server/database configuration option that limits the maximum degree of parallelism for a single query, controlling how many CPU cores SQL Server uses for parallel execution. |
| **MCP (Model Context Protocol)** | An open protocol that standardizes how AI models connect to external data sources and tools, enabling language model agents to query databases and call APIs through a consistent interface. |
| **Memory-Optimized Table** | A table stored entirely in memory using SQL Server's In-Memory OLTP engine, providing extremely low-latency reads and writes with optional disk durability for high-throughput workloads. |
| **MERGE** | A T-SQL statement that performs INSERT, UPDATE, and DELETE operations in a single statement based on a join between a source and target table, often used for upsert (insert-or-update) patterns. |
| **Multi-Statement TVF** | A table-valued function that uses a BEGIN…END block to build and populate a return table variable through multiple statements, less optimizable than inline TVFs because the optimizer cannot inline them. |

---

## N

| Term | Definition |
|------|-----------|
| **Natively Compiled Stored Procedure** | A stored procedure compiled to native machine code at creation time, designed for memory-optimized tables to achieve maximum throughput with minimal interpreted T-SQL overhead. |
| **Node (Graph)** | A table in a SQL graph database declared with `AS NODE`, representing entities in the graph. Each row is an entity, and nodes are connected to other nodes through edge tables. |

---

## O

| Term | Definition |
|------|-----------|
| **OPENJSON** | A T-SQL table-valued function that parses a JSON string and returns rows representing the JSON structure, with columns for key, value, and type, enabling relational queries over JSON data. |
| **Optimistic Concurrency** | A concurrency strategy that assumes conflicts between transactions are rare, allowing reads without locks and detecting conflicts only at commit time, as used by Snapshot Isolation and RCSI. |
| **Ownership Chaining** | A SQL Server mechanism that skips permission checks on referenced objects when the owner of the referencing object (e.g., a stored procedure) also owns the referenced object (e.g., a table). |

---

## P

| Term | Definition |
|------|-----------|
| **Parameter Sniffing** | The optimizer's behavior of using the parameter values from the first execution of a plan to estimate cardinality for all subsequent executions, which can cause poor plans when parameter distributions vary widely. |
| **Partition Elimination** | A query optimization where SQL Server skips scanning partitions whose ranges cannot satisfy the query predicate, significantly reducing I/O for large partitioned tables. |
| **Partition Switching** | A near-instantaneous metadata operation that moves a table partition (or entire table) to a partition in another table, used for efficient bulk load and archival in sliding window patterns. |
| **PERCENT_RANK** | A window function that calculates the relative rank of a row as a percentage between 0 and 1 within the partition, computed as (rank - 1) / (total rows - 1). |
| **Plan Forcing** | A Query Store feature that locks a query to a specific execution plan identified by its plan_id, preventing the optimizer from choosing a different plan even if statistics change. |
| **Plan Guide** | A database object that attaches query hints to a specific query statement without modifying application code, used to fix query plan issues in third-party or unmodifiable applications. |
| **PREDICT** | A T-SQL function (Azure SQL Edge / SQL Server 2017+) that runs an ONNX machine learning model inline within a query, returning predictions from a registered model without external round-trips. |
| **Private Endpoint** | An Azure networking feature that assigns a private IP address from your virtual network to an Azure service (e.g., Azure SQL), keeping traffic off the public internet and within the Azure backbone. |

---

## Q

| Term | Definition |
|------|-----------|
| **Query Store** | A SQL Server and Azure SQL feature that automatically captures query plans and runtime statistics over time, enabling plan regression detection, plan forcing, and performance trend analysis. |

---

## R

| Term | Definition |
|------|-----------|
| **RAG (Retrieval-Augmented Generation)** | An AI architecture that retrieves relevant documents or data from an external store (e.g., vector search in Azure SQL) and provides them as grounding context to a language model before generating a response. |
| **Randomized Encryption** | An Always Encrypted mode that produces different ciphertext each time the same plaintext is encrypted, providing stronger security than Deterministic encryption but preventing equality searches on encrypted columns. |
| **RCSI (Read Committed Snapshot Isolation)** | A database-level setting that causes READ COMMITTED transactions to read the last committed version of a row from the version store instead of waiting for locks, improving read concurrency. |
| **RRF (Reciprocal Rank Fusion)** | A rank aggregation algorithm that combines ranked lists from multiple retrieval methods (e.g., full-text and vector search) by summing reciprocal ranks, used in hybrid search to balance different relevance signals. |
| **ROWVERSION** | A SQL Server data type that automatically generates a unique binary number incremented with each INSERT or UPDATE in the database, used for optimistic concurrency and change tracking. |
| **RLS (Row-Level Security)** | A SQL Server feature that controls which rows a user can access in a table by binding security policies with filter and block predicates to the table, enforced transparently at the engine level. |

---

## S

| Term | Definition |
|------|-----------|
| **SCHEMABINDING** | An option on views, functions, and indexed views that prevents schema changes to referenced objects and is required for creating indexes on views and for deterministic function classification. |
| **Secure Enclave** | A hardware-based trusted execution environment (e.g., Intel SGX) used with Always Encrypted with Secure Enclaves to allow the server to perform operations on encrypted data without exposing plaintext. |
| **Security Policy** | A database object that groups one or more Row-Level Security predicates and is bound to a table, controlling which security functions are applied to filter or block data access. |
| **Sequence** | A database object that generates a sequential numeric series independently of any table, allowing multiple tables or applications to share a single counter with guaranteed uniqueness. |
| **Service Endpoint** | An Azure Virtual Network feature that extends the VNet identity to an Azure service over the Azure backbone, restricting access to only traffic originating from specific subnets. |
| **SHORTEST_PATH** | A graph extension for the MATCH clause that finds the shortest path between two nodes in a directed or undirected graph, used with LAST_NODE and FOR PATH to traverse variable-length relationships. |
| **Sliding Window** | A table partitioning maintenance pattern that adds new empty partitions for future data and archives or removes the oldest partition using partition switching, without locking the active data. |
| **Snapshot Isolation** | A transaction isolation level where a transaction reads a consistent snapshot of the database as it existed at the start of the transaction, using row versions from the version store to avoid reader-writer blocking. |
| **sp_executesql** | A system stored procedure that executes a parameterized T-SQL string, enabling plan reuse by separating the query text from parameter values and avoiding SQL injection risks compared to EXEC with string concatenation. |
| **sp_invoke_external_rest_endpoint** | An Azure SQL system stored procedure that calls an external HTTPS REST endpoint directly from T-SQL, enabling the database to integrate with Azure OpenAI, Azure Functions, and other HTTP APIs. |
| **sqlpackage** | A command-line utility for importing, exporting, publishing, and extracting Azure SQL and SQL Server databases using DACPAC and BACPAC formats, central to CI/CD database deployment pipelines. |
| **SQL Database Projects** | A Visual Studio / VS Code project type (`.sqlproj`) that models a database as a collection of declarative T-SQL object definitions under source control, supporting build, publish, and schema comparison. |

---

## T

| Term | Definition |
|------|-----------|
| **TDE (Transparent Data Encryption)** | Encrypts the data files, log files, and backups of a SQL Server database at rest using a database encryption key, protecting against offline media theft without requiring application changes. |
| **Temporal Table** | A system-versioned table that automatically records the full history of data changes in a linked history table, enabling point-in-time queries using the `FOR SYSTEM_TIME AS OF` clause. |
| **THROW** | A T-SQL statement that raises an exception and transfers execution to a CATCH block or the caller, replacing RAISERROR with cleaner syntax and re-throwing the original error without additional parameters. |
| **Trigger** | A special type of stored procedure that executes automatically in response to DML (INSERT, UPDATE, DELETE) or DDL events on a table or view, used for auditing, validation, and cascading logic. |
| **TRY_CONVERT** | A T-SQL function that attempts a data type conversion and returns NULL on failure instead of raising an error, providing safe conversion handling without TRY/CATCH blocks. |
| **TVF (Table-Valued Function)** | A user-defined function that returns a table result set, available as Inline TVF (single SELECT, optimizer-friendly) or Multi-Statement TVF (imperative logic, less optimizable). |

---

## V

| Term | Definition |
|------|-----------|
| **VECTOR** | A native data type in Azure SQL Database (preview) that stores fixed-dimension floating-point arrays as compact binary, purpose-built for storing and searching embedding vectors. |
| **VECTOR_DISTANCE** | A T-SQL function that computes the distance between two vector values using a specified metric (cosine, euclidean, dot), enabling similarity scoring in queries. |
| **VECTOR_SEARCH** | A T-SQL function or capability in Azure SQL that performs approximate nearest neighbor search over a vector column using a DiskANN index, returning the top-K most similar rows. |
| **Version Store** | A region of tempdb (or the primary filegroup for RCSI in Azure SQL) that stores previous row versions needed by snapshot-based isolation levels and online index operations. |

---

## W

| Term | Definition |
|------|-----------|
| **Window Function** | A T-SQL function that performs calculations across a set of rows related to the current row (the "window"), defined with OVER(PARTITION BY … ORDER BY …), without collapsing rows like aggregate functions do. |

---

## X

| Term | Definition |
|------|-----------|
| **XACT_ABORT** | A session or batch setting that, when ON, causes the entire transaction to roll back automatically when any T-SQL statement raises a runtime error, preventing partial commits in error scenarios. |
| **XACT_STATE** | A T-SQL function that returns the state of the current transaction inside a CATCH block: 1 (active and committable), -1 (active but uncommittable), or 0 (no active transaction). |

---

**[← Back to Appendix](./README.md)**
