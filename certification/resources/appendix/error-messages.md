---
title: Common T-SQL Error Messages
tags:
  - dp-800
  - errors
  - troubleshooting
  - reference
---

# Common T-SQL Error Messages and Solutions

Quick reference for error messages you are likely to encounter in Azure SQL Database and Fabric SQL when developing AI-enabled database solutions.

---

## Constraint & Schema Errors

### Msg 547 — Foreign Key Violation

```text
Msg 547, Level 16, State 0
The INSERT statement conflicted with the FOREIGN KEY constraint "FK_Orders_Customers".
The conflict occurred in database "AdventureWorks", table "dbo.Customers", column "CustomerID".
```

**Cause**: Inserting or updating a row where the referenced parent row does not exist, or deleting a parent row that still has child rows.

**Solution**:

```sql
-- Check parent exists before inserting child
IF EXISTS (SELECT 1 FROM dbo.Customers WHERE CustomerID = 99)
BEGIN
    INSERT INTO dbo.Orders (OrderID, CustomerID) VALUES (1001, 99);
END

-- Or delete children before parent
DELETE FROM dbo.Orders WHERE CustomerID = 99;
DELETE FROM dbo.Customers WHERE CustomerID = 99;
```

---

### Msg 2627 — Unique Constraint Violation (Duplicate Key)

```text
Msg 2627, Level 14, State 1
Violation of UNIQUE KEY constraint "UQ_Employees_Email".
Cannot insert duplicate key in object "dbo.Employees". The duplicate key value is (jane@example.com).
```

**Cause**: An INSERT or UPDATE attempts to store a value that already exists in a column or index defined as UNIQUE or PRIMARY KEY.

**Solution**:

```sql
-- Use INSERT ... WHERE NOT EXISTS to avoid duplicates
INSERT INTO dbo.Employees (EmployeeID, Email)
SELECT 42, 'jane@example.com'
WHERE NOT EXISTS (
    SELECT 1 FROM dbo.Employees WHERE Email = 'jane@example.com'
);

-- Or use MERGE for upsert behavior
MERGE dbo.Employees AS tgt
USING (SELECT 42 AS EmployeeID, 'jane@example.com' AS Email) AS src
ON tgt.Email = src.Email
WHEN NOT MATCHED THEN INSERT (EmployeeID, Email) VALUES (src.EmployeeID, src.Email);
```

---

### Msg 515 — Cannot Insert NULL into NOT NULL Column

```text
Msg 515, Level 16, State 2
Cannot insert the value NULL into column "LastName", table "dbo.Employees"; column does not allow nulls. INSERT fails.
```

**Cause**: An INSERT or UPDATE omits a required column or explicitly passes NULL to a column defined as NOT NULL with no DEFAULT.

**Solution**:

```sql
-- Provide a value for every NOT NULL column
INSERT INTO dbo.Employees (EmployeeID, FirstName, LastName, Email)
VALUES (43, 'John', 'Doe', 'john@example.com');

-- Or add a DEFAULT to the column definition
ALTER TABLE dbo.Employees
    ADD CONSTRAINT DF_Employees_LastName DEFAULT 'Unknown' FOR LastName;
```

---

## JSON Errors

### Msg 13608 — Property Not Found (Strict Mode)

```text
Msg 13608, Level 16, State 5
Property cannot be found on the specified JSON path.
```

**Cause**: `JSON_VALUE` or `JSON_QUERY` is called with the `strict` keyword and the specified path does not exist in the JSON document.

**Solution**:

```sql
DECLARE @json NVARCHAR(MAX) = '{"name": "Alice"}';

-- Use lax (default) to return NULL when path is missing
SELECT JSON_VALUE(@json, 'lax $.age') AS Age;        -- returns NULL

-- Only use strict when the field is guaranteed to exist
SELECT JSON_VALUE(@json, 'strict $.name') AS Name;   -- returns 'Alice'
```

---

### Msg 13609 — JSON Not Properly Formatted

```text
Msg 13609, Level 16, State 2
JSON text is not properly formatted. Unexpected character "'" was found at position 10.
```

**Cause**: The string passed to a JSON function (`ISJSON`, `JSON_VALUE`, `OPENJSON`, etc.) is not valid JSON. Common causes include single quotes, unquoted keys, or trailing commas.

**Solution**:

```sql
-- Validate before parsing
DECLARE @raw NVARCHAR(MAX) = N'{"key": "value"}';

IF ISJSON(@raw) = 1
    SELECT JSON_VALUE(@raw, '$.key');
ELSE
    PRINT 'Invalid JSON: ' + @raw;
```

---

### Msg 13610 — JSON_VALUE Returned Object/Array

```text
Msg 13610, Level 16, State 3
The argument to JSON_VALUE cannot be a JSON object or a JSON array.
```

**Cause**: `JSON_VALUE` is designed for scalar values only. Using it on a path that resolves to a nested object or array returns this error in strict mode (or NULL in lax mode).

**Solution**:

```sql
DECLARE @json NVARCHAR(MAX) = '{"person": {"name": "Alice", "age": 30}}';

-- Wrong: JSON_VALUE on an object path
-- SELECT JSON_VALUE(@json, 'strict $.person');

-- Correct: use JSON_QUERY for objects/arrays
SELECT JSON_QUERY(@json, '$.person') AS PersonObject;

-- Or drill into the scalar directly
SELECT JSON_VALUE(@json, '$.person.name') AS PersonName;
```

---

## Security & Permissions Errors

### Msg 229 — Permission Denied

```text
Msg 229, Level 14, State 5
The EXECUTE permission was denied on the object "usp_GetOrders", database "SalesDB", schema "dbo".
```

**Cause**: The current user or role does not have the required permission (SELECT, INSERT, EXECUTE, etc.) on the target object.

**Solution**:

```sql
-- Grant specific permission to a user or role
GRANT EXECUTE ON dbo.usp_GetOrders TO [AppUser];

-- Or use a database role for grouped access
ALTER ROLE db_datareader ADD MEMBER [AppUser];

-- Verify current permissions
SELECT * FROM fn_my_permissions('dbo.usp_GetOrders', 'OBJECT');
```

---

### Msg 297 — EXECUTE AS Impersonation Denied

```text
Msg 297, Level 16, State 1
The user does not have permission to perform this action. EXECUTE AS failed.
```

**Cause**: The caller does not have IMPERSONATE permission on the target login or user, or the target user does not have a server-level login when using `EXECUTE AS LOGIN`.

**Solution**:

```sql
-- Grant IMPERSONATE on the target user
GRANT IMPERSONATE ON USER::ReportUser TO [AppUser];

-- Or use EXECUTE AS OWNER on the stored procedure
-- so callers inherit the owner's permissions without impersonation
CREATE OR ALTER PROCEDURE dbo.usp_SecureReport
WITH EXECUTE AS OWNER
AS
    SELECT * FROM dbo.SensitiveData;
```

---

### Msg 33280 — Cannot Encrypt Column (Always Encrypted Setup)

```text
Msg 33280, Level 16, State 0
Column "SSN" in table "dbo.Patients" is encrypted using Always Encrypted but the encryption key
has not been provisioned or the driver does not support column encryption.
```

**Cause**: Querying an Always Encrypted column without a driver that supports column encryption, or without the Column Encryption Key (CEK) available in the key store.

**Solution**:

```sql
-- Verify CMK and CEK exist in the database
SELECT name, key_store_provider_name
FROM sys.column_master_keys;

SELECT name, column_master_key_id
FROM sys.column_encryption_keys;

-- In application connection string, enable column encryption:
-- Column Encryption Setting=Enabled;
-- Ensure the client has access to the Azure Key Vault CMK.
```

---

## Concurrency & Transaction Errors

### Msg 1205 — Deadlock Victim

```text
Msg 1205, Level 13, State 51
Transaction (Process ID 67) was deadlocked on lock resources with another process and has been
chosen as the deadlock victim. Rerun the transaction.
```

**Cause**: Two sessions hold locks the other needs, causing a circular wait. SQL Server kills the session with the lower deadlock priority.

**Solution**:

```sql
-- Access tables in a consistent order across all transactions
BEGIN TRANSACTION;
    UPDATE dbo.Accounts SET Balance -= 100 WHERE AccountID = 1;  -- always table A first
    UPDATE dbo.Accounts SET Balance += 100 WHERE AccountID = 2;  -- then table B
COMMIT;

-- Optionally raise deadlock priority to avoid being the victim
SET DEADLOCK_PRIORITY HIGH;

-- Use READ_COMMITTED_SNAPSHOT to reduce lock contention
ALTER DATABASE SalesDB SET READ_COMMITTED_SNAPSHOT ON;
```

---

### Msg 3960 — Snapshot Update Conflict

```text
Msg 3960, Level 16, State 2
Snapshot isolation transaction aborted due to update conflict. You cannot use snapshot isolation
to access table "dbo.Orders" directly or indirectly to update, delete, or insert the row that has
been modified or deleted by another transaction.
```

**Cause**: Under snapshot isolation, another transaction committed a change to the same row after your snapshot began. SQL Server detects the write-write conflict and aborts your transaction.

**Solution**:

```sql
-- Retry the transaction on conflict
BEGIN TRY
    SET TRANSACTION ISOLATION LEVEL SNAPSHOT;
    BEGIN TRANSACTION;
        UPDATE dbo.Orders SET Status = 'Shipped' WHERE OrderID = 5001;
    COMMIT;
END TRY
BEGIN CATCH
    IF ERROR_NUMBER() = 3960
    BEGIN
        IF @@TRANCOUNT > 0 ROLLBACK;
        -- Retry logic or fallback to READ COMMITTED
        PRINT 'Snapshot conflict — retrying under READ COMMITTED';
    END
END CATCH;
```

---

### Msg 3609 — Transaction Ended in Trigger

```text
Msg 3609, Level 16, State 2
The transaction ended in the trigger. The batch has been aborted.
```

**Cause**: A trigger called `ROLLBACK TRANSACTION` or an error caused an implicit rollback inside a trigger body, which terminates the entire outer batch.

**Solution**:

```sql
-- In the trigger, use XACT_STATE() to check before rolling back
CREATE OR ALTER TRIGGER trg_Orders_Insert
ON dbo.Orders AFTER INSERT
AS
BEGIN
    SET NOCOUNT ON;
    IF EXISTS (SELECT 1 FROM inserted WHERE Quantity < 0)
    BEGIN
        IF XACT_STATE() <> 0
            ROLLBACK TRANSACTION;
        RAISERROR('Negative quantity not allowed.', 16, 1);
        RETURN;
    END
END;

-- In calling code, wrap in TRY/CATCH and check @@TRANCOUNT
BEGIN TRY
    INSERT INTO dbo.Orders (OrderID, Quantity) VALUES (9001, -5);
END TRY
BEGIN CATCH
    IF @@TRANCOUNT > 0 ROLLBACK;
    PRINT ERROR_MESSAGE();
END CATCH;
```

---

## Performance & Configuration Errors

### Msg 530 — MAXRECURSION Exceeded

```text
Msg 530, Level 16, State 1
The statement terminated. The maximum recursion 100 has been exhausted before statement completion.
```

**Cause**: A recursive CTE iterated more than the allowed number of levels (default 100). Common with deep organizational hierarchies or accidental infinite recursion due to a missing anchor termination condition.

**Solution**:

```sql
-- Increase MAXRECURSION for deep hierarchies
WITH OrgHierarchy AS (
    SELECT EmployeeID, ManagerID, 1 AS Level
    FROM dbo.Employees
    WHERE ManagerID IS NULL
    UNION ALL
    SELECT e.EmployeeID, e.ManagerID, h.Level + 1
    FROM dbo.Employees e
    JOIN OrgHierarchy h ON e.ManagerID = h.EmployeeID
)
SELECT * FROM OrgHierarchy
OPTION (MAXRECURSION 500);  -- 0 = unlimited (use with caution)
```

---

### Msg 8623 — Query Processor Out of Resources

```text
Msg 8623, Level 16, State 1
The query processor ran out of internal resources and could not produce a query plan.
This is a rare event and only expected for extremely complex queries or queries that reference
a very large number of tables or partitions.
```

**Cause**: The query optimizer exhausted its internal stack or exceeded complexity thresholds — typically queries joining 16+ tables, deeply nested subqueries, or extremely large IN lists.

**Solution**:

```sql
-- Break the query into smaller steps using temp tables
SELECT CustomerID, SUM(Amount) AS TotalSpend
INTO #CustomerTotals
FROM dbo.Orders
GROUP BY CustomerID;

SELECT c.CustomerName, t.TotalSpend
FROM dbo.Customers c
JOIN #CustomerTotals t ON c.CustomerID = t.CustomerID;

DROP TABLE #CustomerTotals;

-- Alternatively, use indexed views or pre-aggregation tables
-- to reduce join complexity at query time.
```

---

### Msg 8645 — Memory Grant Timeout

```text
Msg 8645, Level 17, State 1
A timeout occurred while waiting for memory resources to execute the query in resource pool
"default" (2). Rerun the query.
```

**Cause**: The query requested a large memory grant (for sorts, hashes, or bulk operations) that was not available within the timeout period due to memory pressure on the instance.

**Solution**:

```sql
-- Add indexes to eliminate large sort/hash operations
CREATE INDEX IX_Orders_CustomerDate ON dbo.Orders (CustomerID, OrderDate);

-- Use Resource Governor (on-prem/MI) to cap memory per workload group
-- In Azure SQL, scale up the service tier for more memory

-- Use query hints to reduce grant estimate if statistics are stale
UPDATE STATISTICS dbo.Orders WITH FULLSCAN;

-- Force a smaller grant if the estimate is inflated
SELECT * FROM dbo.Orders ORDER BY OrderDate
OPTION (MAX_GRANT_PERCENT = 10);
```

---

## Partitioning Errors

### Msg 4939 — ALTER TABLE SWITCH Failed (Schema Mismatch)

```text
Msg 4939, Level 16, State 1
ALTER TABLE SWITCH statement failed. The table "dbo.Orders_Archive" is not partitioned.
```

**Cause**: `ALTER TABLE ... SWITCH` requires the source and target tables to have identical column definitions, indexes, constraints, and partitioning scheme. Any mismatch — including a missing partition function, different filegroup, or extra/missing index — causes this error.

**Solution**:

```sql
-- Verify both tables share the same partition function
SELECT t.name, ps.name AS PartitionScheme
FROM sys.tables t
JOIN sys.indexes i ON t.object_id = i.object_id AND i.index_id <= 1
LEFT JOIN sys.partition_schemes ps ON i.data_space_id = ps.data_space_id
WHERE t.name IN ('Orders', 'Orders_Archive');

-- Ensure identical indexes exist on target before switching
CREATE INDEX IX_Orders_Archive_OrderDate
    ON dbo.Orders_Archive (OrderDate)
    ON PartitionScheme_OrderDate(OrderDate);

-- Then switch
ALTER TABLE dbo.Orders
    SWITCH PARTITION 1 TO dbo.Orders_Archive PARTITION 1;
```

---

## Vector & AI Errors

### Vector Dimension Mismatch

```text
Msg 4162, Level 16, State 1
The vector in the row (dimensions = 768) is incompatible with the index vector column
(dimensions = 1536). All vectors must have the same number of dimensions.
```

**Cause**: Embeddings stored in the table were generated with a different model (e.g., `text-embedding-ada-002` at 1536 dimensions) than the model now being used to generate query vectors (e.g., a 768-dimension model), or the column definition specifies a fixed dimension.

**Solution**:

```sql
-- Confirm column definition
SELECT COLUMNPROPERTY(OBJECT_ID('dbo.Documents'), 'Embedding', 'vectorLength') AS Dimensions;

-- Always use the same model for storage and query
-- Re-generate embeddings if the model changes
UPDATE dbo.Documents
SET Embedding = CAST(@new_embedding AS VECTOR(1536))
WHERE DocumentID = 1;

-- For new tables, declare the dimension explicitly
CREATE TABLE dbo.Documents (
    DocumentID   INT PRIMARY KEY,
    Content      NVARCHAR(MAX),
    Embedding    VECTOR(1536)   -- matches text-embedding-3-small output
);
```

---

### sp_invoke_external_rest_endpoint HTTP Error / Timeout

```text
Msg 0, Level 11, State 0
Error invoking external endpoint. HTTP status: 429. Retry after 30 seconds.
```

**Cause**: The external REST endpoint (e.g., Azure OpenAI) returned a non-2xx status code. Common causes: rate limiting (429), authentication failure (401), or network timeout.

**Solution**:

```sql
DECLARE @ret INT, @response NVARCHAR(MAX);

EXEC @ret = sp_invoke_external_rest_endpoint
    @url     = N'https://<endpoint>/openai/deployments/text-embedding-3-small/embeddings?api-version=2024-02-01',
    @method  = 'POST',
    @headers = N'{"Content-Type":"application/json","api-key":"<key>"}',
    @payload = N'{"input":"sample text"}',
    @response = @response OUTPUT;

-- Check return code and HTTP status in the response
IF @ret <> 0 OR JSON_VALUE(@response, '$.response.status.http.code') <> '200'
BEGIN
    PRINT 'REST call failed: ' + JSON_VALUE(@response, '$.response.status.http.code');
    PRINT @response;
    -- Implement exponential back-off for 429 errors
END
```

---

### PREDICT Permission Denied

```text
Msg 229, Level 14, State 5
The EXECUTE permission was denied on the object "PREDICT", database "SalesDB", schema "sys".
```

**Cause**: The user account does not have the `EXECUTE ANY EXTERNAL SCRIPT` server-level permission required to run `PREDICT` with ONNX models in Azure SQL Managed Instance or SQL Server with Machine Learning Services.

**Solution**:

```sql
-- Grant at server level (requires sysadmin)
GRANT EXECUTE ANY EXTERNAL SCRIPT TO [MLUser];

-- Verify the external model is registered
SELECT * FROM sys.external_models;

-- Test with a known working user first
EXECUTE AS USER = 'MLUser';
SELECT * FROM PREDICT(
    MODEL = (SELECT model_data FROM dbo.Models WHERE model_name = 'churn_v1'),
    DATA  = (SELECT feature1, feature2 FROM dbo.Customers WHERE CustomerID = 1),
    RUNTIME = ONNX
) WITH (score FLOAT) AS p;
REVERT;
```

---

## Query Store Errors

### Msg 12429 — Query Store Read-Only Mode

```text
Msg 12429, Level 16, State 1
Query Store is in read-only mode for database "SalesDB" because of internal errors or
because the Query Store storage limit has been reached.
```

**Cause**: The Query Store data file has reached its configured `MAX_STORAGE_SIZE_MB` limit, or internal corruption forced read-only mode. New query plans and runtime statistics are no longer captured.

**Solution**:

```sql
-- Check current Query Store state and size
SELECT desired_state_desc, actual_state_desc,
       current_storage_size_mb, max_storage_size_mb
FROM sys.database_query_store_options;

-- Purge old data to free space
EXEC sys.sp_query_store_flush_db;

ALTER DATABASE SalesDB
    SET QUERY_STORE CLEAR;  -- removes all stored data; use with caution

-- Increase storage limit and re-enable
ALTER DATABASE SalesDB
SET QUERY_STORE (
    OPERATION_MODE        = READ_WRITE,
    MAX_STORAGE_SIZE_MB   = 2048,
    CLEANUP_POLICY        = (STALE_QUERY_THRESHOLD_DAYS = 30),
    SIZE_BASED_CLEANUP_MODE = AUTO
);
```

---

**[← Back to Appendix](./README.md)**
