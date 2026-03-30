---
title: Correlated Queries and Error Handling
type: study-material
tags:
  - dp-800
  - correlated-subquery
  - error-handling
  - try-catch
  - throw
---

# Correlated Queries and Error Handling

## Overview

Correlated subqueries reference the outer query and execute once per outer row. Error handling with `TRY/CATCH` and `THROW` provides structured exception management comparable to application-level try/catch blocks.

## Correlated Subqueries

A correlated subquery references a column from the outer query — it cannot run independently.

### EXISTS / NOT EXISTS

```sql
-- Find customers who have placed at least one order
SELECT c.CustomerId, c.Name
FROM dbo.Customers c
WHERE EXISTS (
    SELECT 1 FROM dbo.Orders o
    WHERE o.CustomerId = c.CustomerId  -- correlation: references outer 'c'
);

-- Find customers with NO orders
SELECT c.CustomerId, c.Name
FROM dbo.Customers c
WHERE NOT EXISTS (
    SELECT 1 FROM dbo.Orders o
    WHERE o.CustomerId = c.CustomerId
);
```

### Scalar Correlated Subquery

```sql
-- Get the most recent order amount for each customer
SELECT
    c.CustomerId,
    c.Name,
    (SELECT TOP 1 o.TotalAmount
     FROM dbo.Orders o
     WHERE o.CustomerId = c.CustomerId
     ORDER BY o.OrderDate DESC) AS LastOrderAmount
FROM dbo.Customers c;
```

### IN / NOT IN with Subquery

```sql
-- Products in categories that have >100 products
SELECT ProductId, Name
FROM dbo.Products
WHERE CategoryId IN (
    SELECT CategoryId FROM dbo.Products
    GROUP BY CategoryId
    HAVING COUNT(*) > 100
);
```

### Correlated UPDATE / DELETE

```sql
-- Update each order's total from order items
UPDATE o
SET o.TotalAmount = (
    SELECT SUM(oi.Quantity * oi.UnitPrice)
    FROM dbo.OrderItems oi
    WHERE oi.OrderId = o.OrderId
)
FROM dbo.Orders o;

-- Delete orphaned order items
DELETE oi
FROM dbo.OrderItems oi
WHERE NOT EXISTS (
    SELECT 1 FROM dbo.Orders o
    WHERE o.OrderId = oi.OrderId
);
```

### APPLY Operators

`CROSS APPLY` and `OUTER APPLY` are more powerful alternatives to correlated subqueries:

```sql
-- CROSS APPLY: like INNER JOIN for TVFs (no match = row excluded)
SELECT c.Name, recent.OrderId, recent.OrderDate
FROM dbo.Customers c
CROSS APPLY (
    SELECT TOP 3 OrderId, OrderDate
    FROM dbo.Orders
    WHERE CustomerId = c.CustomerId
    ORDER BY OrderDate DESC
) AS recent;

-- OUTER APPLY: like LEFT JOIN (no match = NULLs for right side)
SELECT c.Name, last_order.OrderDate
FROM dbo.Customers c
OUTER APPLY (
    SELECT TOP 1 OrderDate
    FROM dbo.Orders
    WHERE CustomerId = c.CustomerId
    ORDER BY OrderDate DESC
) AS last_order;
```

## Error Handling with TRY/CATCH

```sql
BEGIN TRY
    -- Code that might fail
    BEGIN TRANSACTION;

    INSERT INTO dbo.Accounts (AccountId, Balance) VALUES (1, 1000);
    UPDATE dbo.Accounts SET Balance = Balance - 500 WHERE AccountId = 1;

    IF (SELECT Balance FROM dbo.Accounts WHERE AccountId = 1) < 0
        THROW 50001, 'Insufficient funds.', 1;

    COMMIT TRANSACTION;
END TRY
BEGIN CATCH
    IF @@TRANCOUNT > 0
        ROLLBACK TRANSACTION;

    -- Log the error
    INSERT INTO dbo.ErrorLog (
        ErrorNumber, ErrorMessage, ErrorSeverity,
        ErrorProcedure, ErrorLine, OccurredAt
    )
    VALUES (
        ERROR_NUMBER(), ERROR_MESSAGE(), ERROR_SEVERITY(),
        ERROR_PROCEDURE(), ERROR_LINE(), GETUTCDATE()
    );

    -- Re-throw to caller
    THROW;
END CATCH;
```

## THROW vs RAISERROR

```sql
-- THROW: re-raises original error (recommended for SQL 2012+)
THROW;                              -- Re-raise inside CATCH
THROW 50001, 'Custom message.', 1;  -- New error: error_number, message, state

-- RAISERROR: legacy approach
RAISERROR ('Error message', 16, 1);             -- severity 16 = user error
RAISERROR ('Value: %d', 16, 1, @MyVariable);   -- with parameter
```

**THROW vs RAISERROR comparison:**
| Aspect | THROW | RAISERROR |
| :--- | :--- | :--- |
| Re-raise original | `THROW;` preserves original error | Not possible |
| Severity | Always 16 | Configurable |
| Termination | Terminates the batch | Configurable |
| Parameters | No formatting | printf-style formatting |
| Recommended | **Yes (SQL 2012+)** | Legacy |

## Custom Error Numbers

Custom errors must be > 50000 (or 13000+ for informational):

```sql
-- Add to sys.messages for reuse
EXEC sp_addmessage 50001, 16, 'Account balance cannot go negative.';

-- Use with RAISERROR by message number
RAISERROR (50001, 16, 1);
```

## Transaction Management in Error Handling

```sql
CREATE PROCEDURE dbo.usp_SafeOperation
AS
BEGIN
    SET NOCOUNT ON;

    DECLARE @TranCount int = @@TRANCOUNT;

    -- Use savepoint if nested in outer transaction
    IF @TranCount > 0
        SAVE TRANSACTION MySavepoint;
    ELSE
        BEGIN TRANSACTION;

    BEGIN TRY
        -- operations here
        IF @TranCount = 0
            COMMIT TRANSACTION;
    END TRY
    BEGIN CATCH
        IF @TranCount > 0
            ROLLBACK TRANSACTION MySavepoint;  -- partial rollback
        ELSE
            ROLLBACK TRANSACTION;

        THROW;
    END CATCH;
END;
```

## Use Cases

- **EXISTS/NOT EXISTS**: Existence checks; generally faster than `IN` with NULLs
- **CROSS/OUTER APPLY**: Top-N per group, calling inline TVFs per row
- **TRY/CATCH + THROW**: All stored procedures with DML operations
- **Correlated UPDATE**: Refreshing denormalized columns

## Common Issues & Errors

| Issue | Cause | Resolution |
| :--- | :--- | :--- |
| `NOT IN` returns no rows | NULL in subquery result | Use `NOT EXISTS` instead (handles NULLs correctly) |
| `CATCH` not catching | Error severity < 11 or compile error | `TRY/CATCH` only catches runtime errors ≥ severity 11 |
| `THROW` outside `CATCH` | Used without preceding CATCH | Only use bare `THROW;` inside a `CATCH` block |

## Exam Tips

- `NOT EXISTS` is preferred over `NOT IN` when the subquery might return NULLs
- `CROSS APPLY` vs `OUTER APPLY`: same semantics as INNER JOIN vs LEFT JOIN
- `THROW` inside `CATCH` re-raises the original error — preserves error number and message
- `@@TRANCOUNT` > 0 inside a procedure means you're inside a caller's transaction

## Key Takeaways

- Correlated subqueries run once per outer row — use `EXISTS` for existence checks, `APPLY` for row-level TVF calls
- `TRY/CATCH` handles runtime errors ≥ severity 11
- Prefer `THROW` over `RAISERROR` for new code (SQL 2012+)

## Related Topics

- [03-Stored Procedures](../02-programmability-objects/03-stored-procedures.md)
- [01-CTEs & Window Functions](./01-ctes-window-functions.md)

## Official Documentation

- [TRY...CATCH (Transact-SQL)](https://learn.microsoft.com/en-us/sql/t-sql/language-elements/try-catch-transact-sql)
- [THROW (Transact-SQL)](https://learn.microsoft.com/en-us/sql/t-sql/language-elements/throw-transact-sql)
- [Subquery Fundamentals](https://learn.microsoft.com/en-us/sql/relational-databases/performance/subqueries)

---

**[← Previous](./04-graph-queries.md) | [↑ Back to Section](./README.md)**
