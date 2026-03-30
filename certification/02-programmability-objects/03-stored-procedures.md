---
title: Stored Procedures
type: study-material
tags:
  - dp-800
  - stored-procedures
  - t-sql
  - execute-as
---

# Stored Procedures

## Overview

Stored procedures are precompiled T-SQL batches stored in the database. They support parameters (input, output, table-valued), error handling, transaction control, and security context switching.

## Creating Stored Procedures

```sql
CREATE PROCEDURE dbo.usp_GetCustomerOrders
    @CustomerId  int,
    @StartDate   date = NULL,
    @EndDate     date = NULL
AS
BEGIN
    SET NOCOUNT ON;

    SELECT
        o.OrderId,
        o.OrderDate,
        o.TotalAmount
    FROM dbo.Orders o
    WHERE o.CustomerId = @CustomerId
      AND (@StartDate IS NULL OR o.OrderDate >= @StartDate)
      AND (@EndDate   IS NULL OR o.OrderDate <= @EndDate)
    ORDER BY o.OrderDate DESC;
END;
GO

-- Execute
EXEC dbo.usp_GetCustomerOrders @CustomerId = 42, @StartDate = '2025-01-01';
```

## Output Parameters

```sql
CREATE PROCEDURE dbo.usp_CreateOrder
    @CustomerId  int,
    @OrderId     int OUTPUT
AS
BEGIN
    SET NOCOUNT ON;

    INSERT INTO dbo.Orders (CustomerId, OrderDate)
    VALUES (@CustomerId, GETUTCDATE());

    SET @OrderId = SCOPE_IDENTITY();
END;
GO

-- Execute with OUTPUT
DECLARE @NewOrderId int;
EXEC dbo.usp_CreateOrder @CustomerId = 1, @OrderId = @NewOrderId OUTPUT;
SELECT @NewOrderId AS NewOrderId;
```

## Table-Valued Parameters

```sql
-- Create the table type
CREATE TYPE dbo.OrderItemList AS TABLE (
    ProductId   int             NOT NULL,
    Quantity    int             NOT NULL,
    UnitPrice   decimal(10,2)   NOT NULL
);
GO

-- Use it in a procedure
CREATE PROCEDURE dbo.usp_InsertOrderItems
    @OrderId    int,
    @Items      dbo.OrderItemList READONLY
AS
BEGIN
    SET NOCOUNT ON;

    INSERT INTO dbo.OrderItems (OrderId, ProductId, Quantity, UnitPrice)
    SELECT @OrderId, ProductId, Quantity, UnitPrice
    FROM @Items;
END;
GO
```

## Error Handling

```sql
CREATE PROCEDURE dbo.usp_TransferFunds
    @FromAccountId  int,
    @ToAccountId    int,
    @Amount         decimal(18,2)
AS
BEGIN
    SET NOCOUNT ON;

    BEGIN TRANSACTION;
    BEGIN TRY
        UPDATE dbo.Accounts SET Balance -= @Amount WHERE AccountId = @FromAccountId;
        UPDATE dbo.Accounts SET Balance += @Amount WHERE AccountId = @ToAccountId;
        COMMIT TRANSACTION;
    END TRY
    BEGIN CATCH
        ROLLBACK TRANSACTION;
        THROW;  -- Re-raise the error to the caller
    END CATCH;
END;
GO
```

**Error functions in CATCH:**

| Function | Returns |
| :--- | :--- |
| `ERROR_NUMBER()` | SQL error number |
| `ERROR_MESSAGE()` | Error description |
| `ERROR_SEVERITY()` | Severity level (1-25) |
| `ERROR_STATE()` | Error state |
| `ERROR_LINE()` | Line number where error occurred |
| `ERROR_PROCEDURE()` | Procedure name |

## EXECUTE AS — Security Context

`EXECUTE AS` changes the security context for the procedure's execution:

```sql
-- Execute as a specific user
CREATE PROCEDURE dbo.usp_GetSensitiveData
WITH EXECUTE AS 'ReportUser'
AS
BEGIN
    SELECT * FROM dbo.SensitiveTable;  -- runs as ReportUser
END;

-- Execute as the procedure owner (schema owner)
CREATE PROCEDURE dbo.usp_CrossSchemaQuery
WITH EXECUTE AS OWNER
AS
BEGIN
    SELECT * FROM OtherSchema.Table1;
END;
```

**EXECUTE AS options:** `CALLER` (default), `SELF` (creator), `OWNER` (schema owner), `'username'` (specific user)

## Recompilation

```sql
-- Force recompile once (for parameter-sensitive queries)
EXEC dbo.usp_GetCustomerOrders @CustomerId = 42 WITH RECOMPILE;

-- Force recompile every execution (for highly variable data)
CREATE PROCEDURE dbo.usp_VariableQuery
WITH RECOMPILE
AS ...
```

## sp_executesql for Dynamic SQL

Use `sp_executesql` instead of `EXEC(@sql)` for parameterization, plan caching, and SQL injection prevention.

**Why sp_executesql over EXEC(@sql):**

- **Parameterization** — values passed as parameters, not concatenated into the string
- **Plan caching** — same statement hash is reused across calls with different parameter values
- **SQL injection prevention** — user input cannot alter the query structure

**Syntax:** `EXEC sp_executesql @stmt, N'@param1 type, @param2 type', @param1 = value, @param2 = value`

**When you must use dynamic SQL:** dynamic column/table names, dynamic ORDER BY, runtime-determined object names

```sql
-- Unsafe: concatenation = SQL injection risk + no plan reuse
DECLARE @sql NVARCHAR(MAX);
SET @sql = 'SELECT * FROM Orders WHERE CustomerID = ' + @CustomerID;
EXEC(@sql);  -- BAD: no parameterization

-- Safe: sp_executesql with parameters
SET @sql = 'SELECT * FROM Orders WHERE CustomerID = @CustID';
EXEC sp_executesql
    @sql,
    N'@CustID INT',
    @CustID = @CustomerID;  -- GOOD: parameterized, plan cacheable

-- Dynamic table name (must still sanitize)
DECLARE @TableName NVARCHAR(128) = N'Orders';
-- Validate against sys.objects first!
IF NOT EXISTS (SELECT 1 FROM sys.objects WHERE name = @TableName AND type = 'U')
    THROW 50001, 'Invalid table name', 1;
SET @sql = 'SELECT COUNT(*) FROM ' + QUOTENAME(@TableName);
EXEC sp_executesql @sql;
```

## Natively Compiled Stored Procedures

Natively compiled stored procedures are compiled to machine code at creation time, providing extreme performance for OLTP workloads on In-Memory OLTP tables.

**Requirements:**

- `WITH NATIVE_COMPILATION` — compiles to native machine code
- `SCHEMABINDING` — required; prevents schema changes to referenced objects
- References only memory-optimized tables

**Limitations:**

- Limited T-SQL surface area: no temp tables, no cursors, limited JOIN types
- No `TRY/CATCH` — replaced by `ATOMIC` blocks
- No `EXEC` or dynamic SQL within the procedure

**ATOMIC blocks** replace `TRY/CATCH` and wrap all statements in an implicit transaction that either fully commits or fully rolls back.

```sql
CREATE PROCEDURE dbo.usp_InsertOrder
    @CustomerID INT,
    @TotalAmount DECIMAL(18,2)
WITH NATIVE_COMPILATION, SCHEMABINDING
AS
BEGIN ATOMIC WITH (TRANSACTION ISOLATION LEVEL = SNAPSHOT, LANGUAGE = N'English')
    INSERT INTO dbo.OrdersMemoryOptimized (CustomerID, TotalAmount, OrderDate)
    VALUES (@CustomerID, @TotalAmount, GETUTCDATE());
END;
```

## Procedure Plan Caching and Recompilation

SQL Server compiles a query plan on the first execution and caches it for reuse. **Parameter sniffing** means the cached plan is optimized for the first parameter values seen.

**When parameter sniffing is problematic:**

- First call uses an atypical (e.g., low-volume) parameter value
- Resulting plan is poor for subsequent calls with high-volume parameters
- Symptoms: fast for some inputs, slow for others with no schema changes

**Solutions:**

| Option | Behavior | Cost |
| :--- | :--- | :--- |
| `OPTION(RECOMPILE)` | Recompile this query every execution | High — no plan reuse |
| `OPTIMIZE FOR (value)` | Compile plan for a specific value | Low — one plan, may not fit all |
| `OPTIMIZE FOR UNKNOWN` | Use average statistics, not sniffed value | Low — balanced plan |
| Local variable trick | Assign param to local var before use | Low — breaks sniffing, less sharing |
| `WITH RECOMPILE` on proc | Recompile entire procedure every call | High — use sparingly |

```sql
-- OPTION(RECOMPILE) on specific query
SELECT * FROM Orders WHERE CustomerID = @CustomerID
OPTION(RECOMPILE);

-- OPTIMIZE FOR specific value
SELECT * FROM Orders WHERE CustomerID = @CustomerID
OPTION(OPTIMIZE FOR (@CustomerID = 12345));

-- OPTIMIZE FOR UNKNOWN (use average statistics)
SELECT * FROM Orders WHERE CustomerID = @CustomerID
OPTION(OPTIMIZE FOR (@CustomerID UNKNOWN));
```

## Use Cases

- **Encapsulation**: Hide complex logic behind a simple interface
- **Security**: Grant `EXECUTE` on procedure without table access (ownership chaining)
- **Performance**: Compiled once, reused; reduce network round-trips
- **Transactions**: Wrap multi-step operations in a single transaction

## Common Issues & Errors

| Issue | Cause | Resolution |
| :--- | :--- | :--- |
| Parameter sniffing | Cached plan optimized for first parameter value | Use `OPTION (RECOMPILE)` or `OPTIMIZE FOR` |
| Nested transaction issues | Committing a savepoint vs outer transaction | Track `@@TRANCOUNT`; use `SAVE TRANSACTION` for nested |
| `SET NOCOUNT ON` missing | Verbose row count messages sent to client | Always add `SET NOCOUNT ON` in procedures |
| SQL injection via dynamic SQL | User input concatenated into query string | Use `sp_executesql` with parameters; `QUOTENAME` for object names |
| Natively compiled proc errors | Using unsupported T-SQL features | Check In-Memory OLTP supported surface area docs |

## Best Practices

- Always include `SET NOCOUNT ON` to suppress row-count messages and reduce network overhead.
- Use `sp_executesql` for all dynamic SQL; never concatenate user input directly into query strings.
- Prefer `THROW` over `RAISERROR` for re-raising errors — it preserves the original error number and message.
- Use `SCOPE_IDENTITY()` rather than `@@IDENTITY` to avoid cross-trigger identity confusion.
- Add `EXECUTE AS` with least-privilege context when procedures access objects outside the caller's normal permissions.

## Exam Tips

- `THROW` re-raises errors with full fidelity; `RAISERROR` is the older alternative
- `SCOPE_IDENTITY()` returns the last identity inserted in the **current scope** (safer than `@@IDENTITY`)
- Table-valued parameters must be declared `READONLY` in the procedure signature
- `sp_executesql` enables plan reuse for dynamic SQL; `EXEC(@sql)` does not parameterize
- Natively compiled procedures require `ATOMIC` blocks instead of `TRY/CATCH`
- `OPTIMIZE FOR UNKNOWN` is the safest general fix for parameter sniffing — avoids extreme plans

## Key Takeaways

- Stored procedures support input, output, and table-valued parameters
- Use `TRY/CATCH` with `THROW` for robust error handling
- `EXECUTE AS` enables least-privilege access patterns without direct table grants
- `sp_executesql` is always preferred over `EXEC(@sql)` for parameterization and plan caching
- Parameter sniffing can cause inconsistent performance; `OPTIMIZE FOR UNKNOWN` or `OPTION(RECOMPILE)` are the primary fixes
- Natively compiled procedures target In-Memory OLTP and use `ATOMIC` blocks instead of `TRY/CATCH`

## Practice Question

A stored procedure that searches orders by CustomerID performs well for most customers but is very slow for one high-volume customer. The plan was created for a low-volume customer. Which is the BEST fix?

A. Add WITH RECOMPILE to the procedure definition
B. Use OPTION(OPTIMIZE FOR (@CustomerID UNKNOWN)) on the query
C. Rebuild all indexes on the Orders table
D. Use EXEC instead of sp_executesql

> [!success]- Answer
> **B — Use OPTION(OPTIMIZE FOR (@CustomerID UNKNOWN)) on the query**
>
> This is a classic parameter sniffing problem. OPTIMIZE FOR UNKNOWN tells the optimizer to use average statistics rather than the sniffed value, producing a more balanced plan that works reasonably well for all customers. WITH RECOMPILE (A) recompiles every execution which is expensive. Rebuilding indexes (C) doesn't address the plan compilation issue. sp_executesql vs EXEC (D) is about parameterization and injection, not plan selection.

## Related Topics

- [02-Functions](./02-functions.md)
- [04-Triggers](./04-triggers.md)
- [05-Correlated Queries & Error Handling](../03-advanced-tsql/05-correlated-queries-error-handling.md)

## Official Documentation

- [Stored Procedures (SQL Server)](https://learn.microsoft.com/en-us/sql/relational-databases/stored-procedures/stored-procedures-database-engine)
- [EXECUTE AS (Transact-SQL)](https://learn.microsoft.com/en-us/sql/t-sql/statements/execute-as-transact-sql)
- [sp_executesql (Transact-SQL)](https://learn.microsoft.com/en-us/sql/relational-databases/system-stored-procedures/sp-executesql-transact-sql)
- [Natively Compiled Stored Procedures](https://learn.microsoft.com/en-us/sql/relational-databases/in-memory-oltp/natively-compiled-stored-procedures)

---

**[← Previous](./02-functions.md) | [↑ Back to Section](./README.md) | [Next →](./04-triggers.md)**
