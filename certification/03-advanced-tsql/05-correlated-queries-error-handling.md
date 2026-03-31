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

> [!abstract]
> - Covers correlated subqueries, EXISTS/NOT EXISTS, TRY/CATCH error handling, THROW vs RAISERROR, and transaction state
> - Correlated subqueries reference the outer query; EXISTS is usually more efficient than IN for large datasets
> - Key exam topics: XACT_STATE() values, THROW vs RAISERROR behavior, ERROR_* functions inside CATCH

> [!tip] What the Exam Tests
> - `XACT_STATE() = -1` = uncommittable transaction (must ROLLBACK); `= 1` = active committable transaction; `= 0` = no active transaction
> - `THROW` re-raises with the original error number and severity; `RAISERROR` creates a new error message (can specify severity)
> - `EXISTS (SELECT 1 FROM …)` stops scanning as soon as one row is found — more efficient than `IN (SELECT col FROM …)` for correlated checks

---

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

> [!warning] Common Mistake
> Not all errors are catchable in TRY/CATCH — severity 20+ errors (fatal connection-terminating errors) and syntax/compile errors bypass the CATCH block. Always check XACT_STATE() before COMMIT or ROLLBACK inside CATCH; committing with XACT_STATE() = -1 will throw an error.

---

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

---

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

| Feature | THROW | RAISERROR |
| :--- | :--- | :--- |
| Severity | Always 16 | 1–25 (you choose) |
| Re-throw | `THROW;` (no args) | Must repeat all params |
| Can use in CATCH | Yes (re-throw) | Yes |
| Terminates batch | Yes (with XACT_ABORT) | Depends on severity |
| Error number range | 50000+ or any | Any |
| Re-raise original | ==`THROW;` preserves original error== | Not possible |
| Parameters | No formatting | printf-style formatting |
| Recommended | **Modern code (SQL 2012+)** | Legacy |

Re-throw pattern using `THROW` with no arguments:

```sql
BEGIN TRY
    EXEC dbo.SomeRiskyProcedure;
END TRY
BEGIN CATCH
    -- Log the error
    INSERT INTO ErrorLog (Message, Severity, ErrorTime)
    VALUES (ERROR_MESSAGE(), ERROR_SEVERITY(), GETUTCDATE());

    -- Re-throw the original error (THROW with no args)
    THROW;
END CATCH;
```

---

## Custom Error Numbers

Custom errors must be > 50000 (or 13000+ for informational):

```sql
-- Add to sys.messages for reuse
EXEC sp_addmessage 50001, 16, 'Account balance cannot go negative.';

-- Use with RAISERROR by message number
RAISERROR (50001, 16, 1);
```

---

## TRY_PARSE and TRY_CONVERT

Safe conversion functions return `NULL` instead of raising an error on failure — useful for validating input data without error handling overhead.

- **TRY_CONVERT(type, expression)** — returns NULL on failed type conversion
- **TRY_CAST(expression AS type)** — same as TRY_CONVERT but simpler syntax
- **TRY_PARSE(expression AS type USING culture)** — parses strings to date/numeric; locale-aware; returns NULL on failure

```sql
-- TRY_CONVERT: safe type conversion
SELECT TRY_CONVERT(INT, '123'),          -- 123
       TRY_CONVERT(INT, 'abc'),          -- NULL (no error)
       TRY_CONVERT(DATE, '2024-13-01'),  -- NULL (invalid date)
       TRY_CONVERT(DATE, '2024-06-15');  -- 2024-06-15

-- TRY_PARSE: locale-aware string parsing
SELECT TRY_PARSE('June 15, 2024' AS DATE USING 'en-US'),  -- 2024-06-15
       TRY_PARSE('15/06/2024' AS DATE USING 'fr-FR');      -- 2024-06-15

-- Filter rows with valid dates only (no TRY/CATCH needed)
SELECT * FROM StagingImport
WHERE TRY_CONVERT(DATE, EventDateStr) IS NOT NULL;
```

---

## XACT_ABORT and Transaction Behavior

`SET XACT_ABORT ON` causes any runtime error to immediately roll back the entire transaction. The default (`XACT_ABORT OFF`) performs statement-level rollback only, which can leave partial transactions open.

- **Critical for:** stored procedures called from application code; ensures atomicity
- **Interaction with TRY/CATCH:** when `XACT_ABORT ON` fires, the CATCH block can still log the error, but the transaction is doomed (`XACT_STATE() = -1`) and cannot be committed

**XACT_STATE() return values:**

| Value | Meaning |
| :--- | :--- |
| `1` | Active transaction, committable |
| `-1` | ==Active transaction, doomed — must ROLLBACK== |
| `0` | No active transaction |

```sql
-- XACT_ABORT ensures the whole transaction rolls back on any error
SET XACT_ABORT ON;
BEGIN TRANSACTION;
    INSERT INTO Orders VALUES (1, 100.00);
    INSERT INTO OrderItems VALUES (99999, 'A1', 1);  -- FK violation
    -- With XACT_ABORT ON: entire transaction rolls back
    -- Without: only this statement fails, Orders insert persists
COMMIT;

-- XACT_STATE in CATCH block
BEGIN TRY
    BEGIN TRANSACTION;
    -- ... operations ...
    COMMIT;
END TRY
BEGIN CATCH
    IF XACT_STATE() = -1      -- doomed transaction
        ROLLBACK;
    ELSE IF XACT_STATE() = 1  -- active, can commit or rollback
        ROLLBACK;
    THROW;
END CATCH;
```

---

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

---

## Use Cases

- **EXISTS/NOT EXISTS**: Existence checks; generally faster than `IN` with NULLs
- **CROSS/OUTER APPLY**: Top-N per group, calling inline TVFs per row
- **TRY/CATCH + THROW**: All stored procedures with DML operations
- **Correlated UPDATE**: Refreshing denormalized columns
- **TRY_CONVERT/TRY_PARSE**: Validating staging data types without CATCH overhead

---

## Common Issues & Errors

| Issue | Cause | Resolution |
| :--- | :--- | :--- |
| `NOT IN` returns no rows | NULL in subquery result | ==Use `NOT EXISTS` instead (handles NULLs correctly)== |
| `CATCH` not catching | Error severity < 11 or compile error | `TRY/CATCH` only catches runtime errors ≥ severity 11 |
| `THROW` outside `CATCH` | Used without preceding CATCH | Only use bare `THROW;` inside a `CATCH` block |
| Partial transaction after error | `XACT_ABORT OFF` (default) | Set `XACT_ABORT ON` in stored procedures |
| Transaction doomed in CATCH | `XACT_ABORT ON` fired | Check `XACT_STATE() = -1`; must ROLLBACK, cannot COMMIT |

---

## Best Practices

- Always set `SET XACT_ABORT ON` at the top of stored procedures that contain transactions — it guarantees atomicity when errors occur.
- Check `XACT_STATE()` in every CATCH block before deciding to COMMIT or ROLLBACK; a doomed transaction (`-1`) must be rolled back.
- Prefer `THROW` over `RAISERROR` for all new T-SQL code (SQL Server 2012+); bare `THROW;` re-raises the original error with no loss of detail.
- Use `TRY_CONVERT` or `TRY_PARSE` to validate incoming data types in ETL/staging pipelines instead of wrapping each conversion in a TRY/CATCH block.
- Use `NOT EXISTS` rather than `NOT IN` whenever the subquery could return NULLs — `NOT IN` with any NULL in the result set returns zero rows.

---

## Exam Tips

> [!tip] Exam Tips
> - `NOT EXISTS` is preferred over `NOT IN` when the subquery might return NULLs
> - `CROSS APPLY` vs `OUTER APPLY`: same semantics as INNER JOIN vs LEFT JOIN
> - `THROW` inside `CATCH` re-raises the original error — preserves error number and message
> - `@@TRANCOUNT` > 0 inside a procedure means you're inside a caller's transaction
> - `TRY_CONVERT` / `TRY_PARSE` return NULL (not an error) on failed conversion — no TRY/CATCH needed
> - `XACT_STATE() = -1` means the transaction is doomed and can only be rolled back
> - `SET XACT_ABORT ON` causes the full transaction to roll back on any runtime error; without it, only the failing statement is rolled back

---

## Practice Questions

**Practice Question**

A stored procedure uses `TRY/CATCH` but does NOT use `SET XACT_ABORT ON`. An error occurs on the second of three INSERT statements. What is the state of the transaction when execution reaches the CATCH block?

A. The entire transaction has been automatically rolled back
B. Only the second INSERT is rolled back; the first INSERT is still pending
C. All three INSERTs are rolled back
D. The transaction is committed up to the point of the error

> [!success]- Answer
> **B — Only the second INSERT is rolled back; the first INSERT is still pending**
>
> Without `SET XACT_ABORT ON`, a runtime error in a transaction causes statement-level rollback only. The transaction remains open with the first INSERT still pending. This can lead to partial commits if the CATCH block doesn't explicitly ROLLBACK. Always use `SET XACT_ABORT ON` in stored procedures to ensure errors cause a full transaction rollback. Check `XACT_STATE()` in the CATCH block to determine whether the transaction can be committed or must be rolled back.

---

## Key Takeaways

- Correlated subqueries run once per outer row — use `EXISTS` for existence checks, `APPLY` for row-level TVF calls
- `TRY/CATCH` handles runtime errors ≥ severity 11
- Prefer `THROW` over `RAISERROR` for new code (SQL 2012+); bare `THROW;` preserves the original error
- `TRY_CONVERT` and `TRY_PARSE` return NULL on failure — lightweight alternative to TRY/CATCH for type validation
- `SET XACT_ABORT ON` guarantees full transaction rollback on any error; check `XACT_STATE()` in CATCH to handle doomed transactions

---

## Related Topics

- [03-Stored Procedures](../02-programmability-objects/03-stored-procedures.md)
- [01-CTEs & Window Functions](./01-ctes-window-functions.md)

---

## Official Documentation

- [TRY...CATCH (Transact-SQL)](https://learn.microsoft.com/en-us/sql/t-sql/language-elements/try-catch-transact-sql)
- [THROW (Transact-SQL)](https://learn.microsoft.com/en-us/sql/t-sql/language-elements/throw-transact-sql)
- [Subquery Fundamentals](https://learn.microsoft.com/en-us/sql/relational-databases/performance/subqueries)
- [TRY_CONVERT (Transact-SQL)](https://learn.microsoft.com/en-us/sql/t-sql/functions/try-convert-transact-sql)
- [SET XACT_ABORT (Transact-SQL)](https://learn.microsoft.com/en-us/sql/t-sql/statements/set-xact-abort-transact-sql)

---

**[← Previous](./04-graph-queries.md) | [↑ Back to Section](./advanced-tsql.md)**
