---
title: Scalar and Table-Valued Functions
type: study-material
tags:
  - dp-800
  - functions
  - scalar-functions
  - table-valued-functions
  - tvf
---

# Scalar and Table-Valued Functions

## Overview

T-SQL functions encapsulate reusable logic. SQL Server supports scalar functions (return a single value) and table-valued functions (return a result set) — both inline and multi-statement variants.

## Scalar Functions

Scalar functions return a single value and can be used anywhere an expression is valid.

```sql
CREATE FUNCTION dbo.fn_GetFullName (
    @FirstName nvarchar(100),
    @LastName  nvarchar(100)
)
RETURNS nvarchar(200)
WITH SCHEMABINDING
AS
BEGIN
    RETURN LTRIM(RTRIM(@FirstName)) + ' ' + LTRIM(RTRIM(@LastName));
END;
GO

-- Usage
SELECT dbo.fn_GetFullName(FirstName, LastName) AS FullName
FROM dbo.Employees;
```

**Performance warning:** Scalar functions called in WHERE clauses or SELECT lists execute **row by row** — they can prevent parallelism and cause performance issues on large tables. Consider inline TVFs as a performant alternative.

## Inline Table-Valued Functions (iTVF)

Inline TVFs are the most performant function type — they behave like parameterized views and can be inlined by the optimizer.

```sql
CREATE FUNCTION dbo.fn_GetCustomerOrders (@CustomerId int)
RETURNS TABLE
WITH SCHEMABINDING
AS
RETURN
(
    SELECT
        o.OrderId,
        o.OrderDate,
        SUM(oi.Quantity * oi.UnitPrice) AS TotalAmount
    FROM dbo.Orders o
    JOIN dbo.OrderItems oi ON oi.OrderId = o.OrderId
    WHERE o.CustomerId = @CustomerId
    GROUP BY o.OrderId, o.OrderDate
);
GO

-- Usage (CROSS APPLY for correlated usage)
SELECT c.Name, o.OrderId, o.TotalAmount
FROM dbo.Customers c
CROSS APPLY dbo.fn_GetCustomerOrders(c.CustomerId) o;
```

## Multi-Statement Table-Valued Functions (mTVF)

Multi-statement TVFs return a table variable populated by multiple statements — more flexible but less performant (not inlined).

```sql
CREATE FUNCTION dbo.fn_GetOrderHierarchy (@OrderId int)
RETURNS @Result TABLE (
    Level       int,
    ItemId      int,
    Description nvarchar(200),
    Amount      decimal(10,2)
)
AS
BEGIN
    INSERT INTO @Result
    SELECT 1, OrderId, 'Order', TotalAmount
    FROM dbo.Orders WHERE OrderId = @OrderId;

    INSERT INTO @Result
    SELECT 2, oi.ItemId, p.Name, oi.Quantity * oi.UnitPrice
    FROM dbo.OrderItems oi
    JOIN dbo.Products p ON p.ProductId = oi.ProductId
    WHERE oi.OrderId = @OrderId;

    RETURN;
END;
```

## Function Comparison

| Aspect | Scalar | Inline TVF | Multi-Statement TVF |
| :--- | :--- | :--- | :--- |
| Returns | Single value | Table (single SELECT) | Table (multiple statements) |
| Optimizer inlining | No | **Yes** | No |
| Parallelism | Blocked | Allowed | Limited |
| `SCHEMABINDING` | Supported | Supported | Supported |
| Multiple statements | Yes | No | Yes |
| Performance | Slow at scale | **Best** | Moderate |

## Scalar UDF Inlining

SQL Server 2019+ can automatically inline simple scalar functions — check with:

```sql
SELECT is_inlineable FROM sys.sql_modules
WHERE object_id = OBJECT_ID('dbo.fn_GetFullName');
```

## Use Cases

- **Scalar**: Format strings, calculate values, encapsulate business rules
- **Inline TVF**: Parameterized views, replacing `CROSS APPLY` complex subqueries
- **Multi-statement TVF**: Complex multi-step result sets not expressible in a single SELECT

## Common Issues & Errors

| Issue | Cause | Resolution |
| :--- | :--- | :--- |
| Slow query with scalar function | Row-by-row execution, no parallelism | Rewrite as inline TVF or inline the logic |
| mTVF performance poor | No statistics on table variable | Upgrade to SQL 2019+ (table variable deferred compilation) or use `OPTION (RECOMPILE)` |

## Exam Tips

- **Inline TVF is the preferred function type** — it's inlined by the optimizer
- Scalar functions **prevent parallelism** when used in DML or large queries
- Multi-statement TVFs have a fixed cardinality estimate (1 row) by default unless using deferred compilation (SQL 2019+)

## Key Takeaways

- Prefer inline TVFs over scalar functions for set-based operations
- `SCHEMABINDING` prevents accidental breakage from schema changes
- Scalar UDF inlining (SQL 2019+) can automatically optimize simple scalar functions

## Related Topics

- [01-Views](./01-views.md)
- [03-Stored Procedures](./03-stored-procedures.md)
- [01-CTEs & Window Functions](../03-advanced-tsql/01-ctes-window-functions.md)

## Official Documentation

- [User-Defined Functions](https://learn.microsoft.com/en-us/sql/relational-databases/user-defined-functions/user-defined-functions)
- [Scalar UDF Inlining](https://learn.microsoft.com/en-us/sql/relational-databases/user-defined-functions/scalar-udf-inlining)

---

**[← Previous](./01-views.md) | [↑ Back to Section](./README.md) | [Next →](./03-stored-procedures.md)**
