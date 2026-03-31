---
title: "T-SQL Core Commands — Quick Reference"
type: cheat-sheet
tags:
  - dp-800
  - cheat-sheet
  - tsql
  - ddl
  - dml
---

# T-SQL Core Commands — Quick Reference

Compact reference for the most frequently tested T-SQL commands on the DP-800 exam.

> [!abstract] Quick Reference
> - Core DDL (CREATE/ALTER TABLE, indexes, partitioning) and DML (INSERT, UPDATE, DELETE, MERGE) syntax
> - Window functions, CTEs, APPLY, PIVOT, and control flow patterns
> - Use during practice questions when you need to quickly verify T-SQL syntax

---

## DDL — Data Definition Language

> [!info] DDL commands define and modify database structure — tables, indexes, constraints, and partitions.

### CREATE TABLE

```sql
CREATE TABLE dbo.Orders (
    OrderID        INT           IDENTITY(1,1) NOT NULL,
    CustomerID     INT           NOT NULL,
    OrderDate      DATETIME2(3)  NOT NULL DEFAULT SYSUTCDATETIME(),
    TotalAmount    DECIMAL(18,2) NOT NULL,
    OrderData      NVARCHAR(MAX) NULL,       -- JSON column
    CONSTRAINT PK_Orders PRIMARY KEY CLUSTERED (OrderID),
    CONSTRAINT FK_Orders_Customer
        FOREIGN KEY (CustomerID) REFERENCES dbo.Customers(CustomerID),
    CONSTRAINT CK_Orders_Amount CHECK (TotalAmount >= 0)
);
```

### ALTER TABLE

```sql
-- Add column
ALTER TABLE dbo.Orders ADD Status NVARCHAR(20) NOT NULL DEFAULT 'Pending';

-- Add constraint
ALTER TABLE dbo.Orders ADD CONSTRAINT CK_Orders_Status
    CHECK (Status IN ('Pending', 'Shipped', 'Delivered', 'Cancelled'));

-- Drop column
ALTER TABLE dbo.Orders DROP COLUMN Status;

-- Drop constraint
ALTER TABLE dbo.Orders DROP CONSTRAINT CK_Orders_Status;
```

### CREATE INDEX

```sql
-- Nonclustered index
CREATE NONCLUSTERED INDEX IX_Orders_CustomerID
    ON dbo.Orders (CustomerID)
    INCLUDE (OrderDate, TotalAmount);

-- Filtered index
CREATE NONCLUSTERED INDEX IX_Orders_Pending
    ON dbo.Orders (OrderDate)
    WHERE Status = 'Pending';

-- Unique index
CREATE UNIQUE NONCLUSTERED INDEX UQ_Customers_Email
    ON dbo.Customers (Email)
    WHERE Email IS NOT NULL;

-- Columnstore index
CREATE NONCLUSTERED COLUMNSTORE INDEX NCCI_Orders_Analytics
    ON dbo.Orders (OrderDate, TotalAmount, CustomerID);
```

### CREATE/ALTER SEQUENCE

```sql
CREATE SEQUENCE dbo.InvoiceSeq
    AS INT
    START WITH 1000
    INCREMENT BY 1
    MINVALUE 1000
    MAXVALUE 9999999
    CYCLE
    CACHE 50;

-- Use in INSERT
INSERT INTO dbo.Invoices (InvoiceNumber, Amount)
VALUES (NEXT VALUE FOR dbo.InvoiceSeq, 250.00);
```

### Temporal Tables

```sql
CREATE TABLE dbo.Products (
    ProductID    INT           NOT NULL PRIMARY KEY,
    ProductName  NVARCHAR(100) NOT NULL,
    Price        DECIMAL(10,2) NOT NULL,
    ValidFrom    DATETIME2 GENERATED ALWAYS AS ROW START NOT NULL,
    ValidTo      DATETIME2 GENERATED ALWAYS AS ROW END   NOT NULL,
    PERIOD FOR SYSTEM_TIME (ValidFrom, ValidTo)
) WITH (SYSTEM_VERSIONING = ON (
    HISTORY_TABLE = dbo.ProductsHistory
));
```

### Partitioning

```sql
-- 1. Partition function
CREATE PARTITION FUNCTION pf_OrderDate (DATETIME2)
    AS RANGE RIGHT FOR VALUES ('2024-01-01', '2025-01-01', '2026-01-01');

-- 2. Partition scheme
CREATE PARTITION SCHEME ps_OrderDate
    AS PARTITION pf_OrderDate
    TO (fg_archive, fg_2024, fg_2025, fg_2026);

-- 3. Create table on scheme
CREATE TABLE dbo.OrdersPartitioned (
    OrderID   INT       NOT NULL,
    OrderDate DATETIME2 NOT NULL,
    Amount    DECIMAL(18,2),
    CONSTRAINT PK_OrdersPart PRIMARY KEY (OrderID, OrderDate)
) ON ps_OrderDate (OrderDate);
```

---

## DML — Data Manipulation Language

> [!info] DML commands manipulate data — INSERT, UPDATE, DELETE, and MERGE are the core operations.

### INSERT Patterns

```sql
-- Standard INSERT
INSERT INTO dbo.Customers (Name, Email)
VALUES ('Alice', 'alice@example.com');

-- Multi-row INSERT
INSERT INTO dbo.Customers (Name, Email)
VALUES ('Bob', 'bob@example.com'),
       ('Carol', 'carol@example.com');

-- INSERT ... SELECT
INSERT INTO dbo.CustomerArchive (CustomerID, Name, Email)
SELECT CustomerID, Name, Email
FROM dbo.Customers
WHERE IsActive = 0;

-- INSERT ... OUTPUT
INSERT INTO dbo.Orders (CustomerID, TotalAmount)
OUTPUT inserted.OrderID, inserted.CustomerID
VALUES (1, 99.99);
```

### UPDATE with JOIN

```sql
UPDATE o
SET o.Status = 'VIP'
FROM dbo.Orders o
INNER JOIN dbo.Customers c ON o.CustomerID = c.CustomerID
WHERE c.TotalSpend > 10000;
```

### DELETE with OUTPUT

```sql
DELETE FROM dbo.Orders
OUTPUT deleted.OrderID, deleted.CustomerID, deleted.TotalAmount
    INTO dbo.DeletedOrdersLog
WHERE OrderDate < DATEADD(YEAR, -7, GETUTCDATE());
```

### MERGE

```sql
MERGE dbo.Products AS tgt
USING dbo.StagingProducts AS src
    ON tgt.ProductID = src.ProductID
WHEN MATCHED AND tgt.Price <> src.Price THEN
    UPDATE SET tgt.Price = src.Price,
               tgt.ModifiedDate = SYSUTCDATETIME()
WHEN NOT MATCHED BY TARGET THEN
    INSERT (ProductID, ProductName, Price)
    VALUES (src.ProductID, src.ProductName, src.Price)
WHEN NOT MATCHED BY SOURCE THEN
    DELETE
OUTPUT $action, inserted.ProductID, deleted.ProductID;
```

> [!tip] Exam Tip
> MERGE requires a semicolon terminator and always needs an ON clause. The three WHEN clauses (MATCHED, NOT MATCHED BY TARGET, NOT MATCHED BY SOURCE) map to UPDATE, INSERT, and DELETE respectively.

---

## Query Patterns

> [!info] These query patterns appear frequently on the exam — especially **window functions** and CTEs.

### Window Functions

```sql
SELECT
    OrderID,
    CustomerID,
    TotalAmount,
    ROW_NUMBER() OVER (PARTITION BY CustomerID ORDER BY OrderDate DESC) AS RowNum,
    RANK()       OVER (ORDER BY TotalAmount DESC)                      AS AmtRank,
    DENSE_RANK() OVER (ORDER BY TotalAmount DESC)                      AS DenseRank,
    NTILE(4)     OVER (ORDER BY TotalAmount DESC)                      AS Quartile,
    SUM(TotalAmount) OVER (
        PARTITION BY CustomerID
        ORDER BY OrderDate
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) AS RunningTotal,
    LAG(TotalAmount, 1, 0)  OVER (PARTITION BY CustomerID ORDER BY OrderDate) AS PrevAmt,
    LEAD(TotalAmount, 1, 0) OVER (PARTITION BY CustomerID ORDER BY OrderDate) AS NextAmt
FROM dbo.Orders;
```

> [!tip] Exam Tip
> ROW_NUMBER always produces unique values; RANK can produce ties with gaps; DENSE_RANK produces ties without gaps. Know the ROWS vs RANGE framing difference for running totals.

### Common Table Expressions (CTEs)

```sql
-- Recursive CTE: org chart
WITH OrgChart AS (
    -- Anchor
    SELECT EmployeeID, ManagerID, Name, 0 AS Level
    FROM dbo.Employees
    WHERE ManagerID IS NULL

    UNION ALL

    -- Recursive
    SELECT e.EmployeeID, e.ManagerID, e.Name, oc.Level + 1
    FROM dbo.Employees e
    INNER JOIN OrgChart oc ON e.ManagerID = oc.EmployeeID
)
SELECT * FROM OrgChart
OPTION (MAXRECURSION 100);
```

### APPLY Operator

```sql
-- CROSS APPLY: like INNER JOIN to a function
SELECT c.CustomerID, c.Name, t.OrderID, t.TotalAmount
FROM dbo.Customers c
CROSS APPLY (
    SELECT TOP 3 OrderID, TotalAmount
    FROM dbo.Orders o
    WHERE o.CustomerID = c.CustomerID
    ORDER BY o.TotalAmount DESC
) t;

-- OUTER APPLY: like LEFT JOIN to a function
SELECT c.CustomerID, c.Name, t.OrderID
FROM dbo.Customers c
OUTER APPLY (
    SELECT TOP 1 OrderID
    FROM dbo.Orders o
    WHERE o.CustomerID = c.CustomerID
    ORDER BY o.OrderDate DESC
) t;
```

> [!warning] Common Mistake
> CROSS APPLY excludes outer rows with no match (like INNER JOIN), while OUTER APPLY includes them with NULLs (like LEFT JOIN). Confusing the two changes your result set.

### PIVOT / UNPIVOT

```sql
-- PIVOT
SELECT CustomerID, [2024], [2025], [2026]
FROM (
    SELECT CustomerID, YEAR(OrderDate) AS OrderYear, TotalAmount
    FROM dbo.Orders
) src
PIVOT (
    SUM(TotalAmount) FOR OrderYear IN ([2024], [2025], [2026])
) pvt;
```

---

## Control Flow

> [!info] Control flow structures manage conditional logic, loops, and error handling in T-SQL batches.

```sql
-- IF / ELSE
IF EXISTS (SELECT 1 FROM dbo.Orders WHERE CustomerID = @CustID)
    PRINT 'Customer has orders';
ELSE
    PRINT 'No orders found';

-- WHILE loop
DECLARE @i INT = 1;
WHILE @i <= 10
BEGIN
    -- process batch @i
    SET @i += 1;
END;

-- TRY / CATCH
BEGIN TRY
    BEGIN TRANSACTION;
    -- operations here
    COMMIT;
END TRY
BEGIN CATCH
    IF @@TRANCOUNT > 0 ROLLBACK;

    THROW;  -- re-raise (preferred over RAISERROR)
END CATCH;
```

### THROW vs RAISERROR

| Feature | THROW | RAISERROR |
| :--- | :--- | :--- |
| Minimum severity | Always 16 | Configurable (0-25) |
| Honors SET XACT_ABORT | Yes | Only severity >= 11 |
| Requires msg_id in sys.messages | No | Yes (with msg_id form) |
| Terminates batch | Yes (when used without params in CATCH) | Only severity >= 20 |
| Recommended for new code | ==Yes== | No |

> [!warning] Common Mistake
> THROW without parameters re-raises the current error only inside a CATCH block. Using THROW outside CATCH without parameters causes a syntax error — use THROW with explicit msg_id, message, and state instead.

---

## Session & Transaction

> [!info] Session settings control isolation levels, transaction behavior, and error handling for the connection.

```sql
-- Set isolation level
SET TRANSACTION ISOLATION LEVEL READ COMMITTED;        -- default
SET TRANSACTION ISOLATION LEVEL SNAPSHOT;               -- optimistic, requires DB setting
-- READ_COMMITTED_SNAPSHOT is not a session-level setting;
-- enable at the database level: ALTER DATABASE ... SET READ_COMMITTED_SNAPSHOT ON

-- XACT_ABORT: auto-rollback on any error
SET XACT_ABORT ON;

-- Check open transactions
SELECT @@TRANCOUNT;

-- Savepoints
BEGIN TRANSACTION;
    SAVE TRANSACTION sp1;
    -- some work
    ROLLBACK TRANSACTION sp1;  -- partial rollback
COMMIT;
```

---

## Metadata Queries

> [!info] System catalog views let you inspect table structure, indexes, columns, and foreign keys programmatically.

```sql
-- List tables and row counts
SELECT s.name AS SchemaName, t.name AS TableName,
       SUM(p.rows) AS RowCount
FROM sys.tables t
JOIN sys.schemas s ON t.schema_id = s.schema_id
JOIN sys.partitions p ON t.object_id = p.object_id AND p.index_id IN (0, 1)
GROUP BY s.name, t.name
ORDER BY RowCount DESC;

-- List indexes on a table
SELECT i.name, i.type_desc, i.is_unique, i.is_primary_key
FROM sys.indexes i
WHERE i.object_id = OBJECT_ID('dbo.Orders');

-- List columns with types
SELECT c.name, t.name AS DataType, c.max_length, c.is_nullable
FROM sys.columns c
JOIN sys.types t ON c.user_type_id = t.user_type_id
WHERE c.object_id = OBJECT_ID('dbo.Orders');

-- List foreign keys
SELECT fk.name, OBJECT_NAME(fk.parent_object_id) AS ChildTable,
       OBJECT_NAME(fk.referenced_object_id) AS ParentTable
FROM sys.foreign_keys fk;

-- Check database compatibility level
SELECT name, compatibility_level FROM sys.databases;
```

---

## String Functions Cheat Table

> [!info] String functions are commonly tested — pay special attention to STRING_AGG, STRING_SPLIT, and TRANSLATE.

| Function | Example | Result |
| :--- | :--- | :--- |
| `LEN()` | `LEN('hello')` | 5 |
| `DATALENGTH()` | `DATALENGTH(N'hello')` | 10 (bytes) |
| `LEFT()` / `RIGHT()` | `LEFT('hello', 3)` | `hel` |
| `SUBSTRING()` | `SUBSTRING('hello', 2, 3)` | `ell` |
| `CHARINDEX()` | `CHARINDEX('ll', 'hello')` | 3 |
| `REPLACE()` | `REPLACE('hello', 'l', 'r')` | `herro` |
| `TRANSLATE()` | `TRANSLATE('2+3', '+-', '  ')` | `2 3` |
| ==`STRING_AGG()`== | `STRING_AGG(Name, ', ')` | Comma-delimited |
| `STRING_SPLIT()` | `STRING_SPLIT('a,b,c', ',')` | 3 rows |
| `TRIM()` | `TRIM('  hi  ')` | `hi` |
| `FORMAT()` | `FORMAT(1234.5, 'C', 'en-US')` | `$1,234.50` |
| `SOUNDEX()` | `SOUNDEX('Smith')` | `S530` |
| `DIFFERENCE()` | `DIFFERENCE('Smith','Smyth')` | 4 (very similar) |

---

## Date Functions Cheat Table

> [!info] Date functions appear in nearly every query scenario — know the difference between DATEPART and DATENAME.

| Function | Example | Notes |
| :--- | :--- | :--- |
| `GETDATE()` | Local server time | `DATETIME` |
| `GETUTCDATE()` | UTC time | `DATETIME` |
| ==`SYSUTCDATETIME()`== | UTC time | `DATETIME2(7)` — preferred |
| `DATEADD()` | `DATEADD(DAY, 7, @d)` | Add interval |
| `DATEDIFF()` | `DATEDIFF(DAY, @start, @end)` | Returns INT |
| `DATEDIFF_BIG()` | Same, returns BIGINT | For large ranges |
| `DATEPART()` | `DATEPART(WEEKDAY, @d)` | Returns INT |
| `DATENAME()` | `DATENAME(MONTH, @d)` | Returns NVARCHAR |
| `EOMONTH()` | `EOMONTH(@d)` | Last day of month |
| `DATEFROMPARTS()` | `DATEFROMPARTS(2025, 6, 15)` | Build a date |
| `FORMAT()` | `FORMAT(@d, 'yyyy-MM-dd')` | Flexible but slow |

---

## Gotchas & Traps

- **ROW_NUMBER vs RANK vs DENSE_RANK on ties:** ROW_NUMBER = always unique (arbitrary tiebreak); RANK = leaves gaps (1,1,3); DENSE_RANK = no gaps (1,1,2). The exam tests which behaves which way.
- **Recursive CTE requires UNION ALL** — not UNION. The anchor and recursive members must be combined with UNION ALL. Forgetting MAXRECURSION causes infinite loops.
- **MERGE requires a unique match** — if multiple source rows match one target row, MERGE throws an error. Deduplicate source before MERGE.
- **CROSS APPLY vs OUTER APPLY** — CROSS APPLY = like INNER JOIN (drops rows with no result from TVF); OUTER APPLY = like LEFT JOIN (keeps rows even if TVF returns nothing).
- **sp_executesql is parameterized** — use it instead of EXEC for dynamic SQL to prevent injection and enable plan reuse. `EXEC(@sql)` is not parameterized.
- **IDENTITY is table-bound; SEQUENCE is independent** — SEQUENCE can be shared across tables, cycled, incremented by any value, and reset. IDENTITY cannot.
- **TRY/CATCH does not catch all errors** — severity 20+ (fatal) and some compilation errors are not catchable. Always check `XACT_STATE()` inside CATCH: -1 = uncommittable, must ROLLBACK.

---

## Before the Exam, I Can…

- [ ] Write a recursive CTE with anchor member, UNION ALL, and recursive member
- [ ] Explain the difference between ROW_NUMBER, RANK, and DENSE_RANK when rows tie
- [ ] Write a window function with PARTITION BY, ORDER BY, and a ROWS/RANGE frame clause
- [ ] Explain when to use CROSS APPLY vs OUTER APPLY
- [ ] Write a MERGE statement with WHEN MATCHED, WHEN NOT MATCHED BY TARGET, WHEN NOT MATCHED BY SOURCE
- [ ] Explain why sp_executesql is preferred over EXEC for dynamic SQL
- [ ] Describe what XACT_STATE() returns and when to use it in a CATCH block

---

**[← Back to Cheat Sheets](./cheat-sheets.md)**
