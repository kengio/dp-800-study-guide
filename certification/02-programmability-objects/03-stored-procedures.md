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

## Exam Tips

- `THROW` re-raises errors with full fidelity; `RAISERROR` is the older alternative
- `SCOPE_IDENTITY()` returns the last identity inserted in the **current scope** (safer than `@@IDENTITY`)
- Table-valued parameters must be declared `READONLY` in the procedure signature

## Key Takeaways

- Stored procedures support input, output, and table-valued parameters
- Use `TRY/CATCH` with `THROW` for robust error handling
- `EXECUTE AS` enables least-privilege access patterns without direct table grants

## Related Topics

- [02-Functions](./02-functions.md)
- [04-Triggers](./04-triggers.md)
- [05-Correlated Queries & Error Handling](../03-advanced-tsql/05-correlated-queries-error-handling.md)

## Official Documentation

- [Stored Procedures (SQL Server)](https://learn.microsoft.com/en-us/sql/relational-databases/stored-procedures/stored-procedures-database-engine)
- [EXECUTE AS (Transact-SQL)](https://learn.microsoft.com/en-us/sql/t-sql/statements/execute-as-transact-sql)

---

**[← Previous](./02-functions.md) | [↑ Back to Section](./README.md) | [Next →](./04-triggers.md)**
