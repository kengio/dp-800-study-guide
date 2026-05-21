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

> [!abstract]
>
> - Covers scalar UDFs, inline TVFs, multi-statement TVFs, and determinism
> - Inline TVFs are expanded like views (optimizer-transparent); multi-statement TVFs are black boxes
> - Key exam topics: inline vs multi-statement TVF performance, deterministic vs non-deterministic, SCHEMABINDING

> [!tip] What the Exam Tests
>
> - **Inline TVF** = single SELECT statement, expanded like a view, allows parallelism, better cardinality estimates
> - **Multi-statement TVF** = explicit RETURN TABLE variable, black box to optimizer, no parallelism
> - Scalar UDFs historically inhibit parallelism — SQL Server 2019+ can inline some scalar UDFs automatically (Intelligent Query Processing)

---

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

> [!warning] Common Mistake
> Scalar UDFs called in WHERE clauses or SELECT lists execute once per row and prevent parallelism in older compatibility levels. The exam may ask which function type is best for performance — prefer inline TVFs over scalar UDFs or multi-statement TVFs.

---

## Inline Table-Valued Functions (iTVF)

**Inline TVFs** are the most performant function type — they behave like parameterized views and can be inlined by the optimizer.

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

---

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

---

## Function Comparison

| Aspect | Scalar | Inline TVF | Multi-Statement TVF |
| :--- | :--- | :--- | :--- |
| Returns | Single value | Table (single SELECT) | Table (multiple statements) |
| Optimizer inlining | No | ==**Yes**== | No |
| Parallelism | Blocked | Allowed | Limited |
| `SCHEMABINDING` | Supported | Supported | Supported |
| Multiple statements | Yes | No | Yes |
| Performance | Slow at scale | **Best** | Moderate |

---

## Scalar UDF Inlining

SQL Server 2019+ can automatically inline simple scalar functions — check with:

```sql
SELECT is_inlineable FROM sys.sql_modules
WHERE object_id = OBJECT_ID('dbo.fn_GetFullName');
```

---

## Inline vs. Multi-Statement TVF Performance

The key difference between inline TVFs (ITVFs) and multi-statement TVFs (MSTVFs) is **optimizer visibility**.

**Inline TVF — optimizer can look inside:**

- A single `SELECT` statement; the optimizer treats it as a "parameterized view"
- Statistics on the underlying tables are available, so cardinality estimates are accurate
- Can be inlined into the calling query's execution plan

**Multi-statement TVF — optimizer cannot look inside:**

- Populates a table variable through multiple statements; the body is a black box
- Optimizer uses a **fixed row count estimate**: 1 row (SQL Server 2012 and earlier) or 100 rows (SQL Server 2014–2016)
- SQL Server 2019+ introduces **table variable deferred compilation**, which improves estimates but still requires a first execution

**Cardinality estimation problem:** When an MSTVF returns thousands of rows but the optimizer estimates 100, downstream operators (joins, sorts, aggregates) are sized incorrectly. This causes memory grant underestimates, spills to tempdb, and poor join strategies.

**Guideline:** Prefer ITVF unless you genuinely need multi-step logic that cannot be expressed in a single SELECT.

```sql
-- ITVF: optimizer can look inside
CREATE FUNCTION dbo.fn_GetCustomerOrders(@CustomerID INT)
RETURNS TABLE
AS
RETURN (
    SELECT OrderID, OrderDate, TotalAmount
    FROM Orders
    WHERE CustomerID = @CustomerID
    AND Status = 'Active'
);

-- MSTVF: optimizer can't see inside, bad cardinality
CREATE FUNCTION dbo.fn_GetOrderDetails(@CustomerID INT)
RETURNS @Result TABLE (OrderID INT, Total DECIMAL(18,2))
AS
BEGIN
    INSERT @Result
    SELECT OrderID, TotalAmount FROM Orders WHERE CustomerID = @CustomerID;
    -- further manipulations...
    RETURN;
END;
```

---

## APPLY Operator with Table-Valued Functions

`APPLY` evaluates a TVF (or subquery) for each row of the left-side table expression. There are two variants:

- **CROSS APPLY** — like an `INNER JOIN`; only returns rows where the TVF returns at least one result
- **OUTER APPLY** — like a `LEFT JOIN`; returns all left-side rows, with NULLs for columns where the TVF returns nothing

**Key use case:** Call a per-row function for each row in a result set, or retrieve a variable number of related rows per parent row.

```sql
-- CROSS APPLY: get top 3 orders per customer
SELECT c.CustomerID, c.Name, o.OrderID, o.TotalAmount
FROM Customers c
CROSS APPLY (
    SELECT TOP 3 OrderID, TotalAmount
    FROM Orders
    WHERE CustomerID = c.CustomerID
    ORDER BY TotalAmount DESC
) o;

-- OUTER APPLY with inline TVF
SELECT c.CustomerID, c.Name, latest.LastOrderDate
FROM Customers c
OUTER APPLY dbo.fn_GetLatestOrder(c.CustomerID) latest;
```

`CROSS APPLY` with a subquery replaces correlated subqueries that reference outer columns and is the idiomatic way to join a TVF to a table.

---

## Function Determinism

A function is **deterministic** if it always returns the same result given the same inputs and the same database state. A function is **non-deterministic** if its result can vary.

| Category | Examples |
| :--- | :--- |
| Deterministic | `LEN`, `DATEADD`, `ROUND`, `UPPER`, `ABS` |
| Non-deterministic | ==`GETDATE`, `NEWID`, `RAND`, `@@ROWCOUNT`== |

**Why it matters:**

- Indexed computed columns require deterministic functions (with `SCHEMABINDING`)
- Indexed views require all referenced functions to be deterministic
- Non-deterministic functions in queries prevent certain optimizer rewrites

Check whether a UDF is deterministic:

```sql
SELECT OBJECTPROPERTY(OBJECT_ID('dbo.MyFunc'), 'IsDeterministic');
-- Returns 1 (deterministic) or 0 (non-deterministic)
```

`SCHEMABINDING` is required for a UDF to be considered deterministic by SQL Server — without it, the engine assumes the function might reference non-bound objects and marks it non-deterministic.

---

## SCHEMABINDING for Functions

`WITH SCHEMABINDING` binds the function to the database objects it references. This prevents those objects from being dropped or altered in ways that would break the function.

**Required when:**

- The function is used in a computed column that has an index
- The function is referenced by an indexed view
- The function is called from another schema-bound object

**Rules:**

- All referenced tables and views must be specified with two-part names: `dbo.TableName`
- Add `WITH SCHEMABINDING` after the `RETURNS` clause (scalar) or `RETURNS TABLE` clause (inline TVF)
- Without `SCHEMABINDING`, the function cannot be marked deterministic, which blocks use in indexed computed columns

```sql
CREATE FUNCTION dbo.fn_FormatPhone(@Phone nvarchar(20))
RETURNS nvarchar(20)
WITH SCHEMABINDING
AS
BEGIN
    RETURN '(' + LEFT(@Phone,3) + ') ' + SUBSTRING(@Phone,4,3) + '-' + RIGHT(@Phone,4);
END;
```

---

## Use Cases

- **Scalar**: Format strings, calculate values, encapsulate business rules
- **Inline TVF**: Parameterized views, replacing `CROSS APPLY` complex subqueries
- **Multi-statement TVF**: Complex multi-step result sets not expressible in a single SELECT

---

## Common Issues & Errors

| Issue | Cause | Resolution |
| :--- | :--- | :--- |
| Slow query with scalar function | Row-by-row execution, no parallelism | ==Rewrite as inline TVF or inline the logic== |
| mTVF performance poor | No statistics on table variable | Upgrade to SQL 2019+ (table variable deferred compilation) or use `OPTION (RECOMPILE)` |
| Cannot create index on computed column | Function not deterministic or missing SCHEMABINDING | Add `WITH SCHEMABINDING` and ensure all referenced objects use two-part names |
| CROSS APPLY returns fewer rows than expected | Using CROSS APPLY instead of OUTER APPLY | Switch to OUTER APPLY to preserve rows where the TVF returns no results |

---

## Best Practices

- Prefer **inline TVFs over scalar functions** for any set-based operation — ITVFs allow parallelism and optimizer inlining
- Always add `WITH SCHEMABINDING` to functions used in computed columns, indexed views, or other schema-bound objects
- Avoid MSTVFs for high-volume queries; if you must use them, add `OPTION (RECOMPILE)` or upgrade to SQL Server 2019+ to benefit from deferred compilation
- Use **CROSS APPLY** (not a correlated subquery) when calling a TVF for each row of a driving table — it's cleaner and often faster
- Test function determinism with `OBJECTPROPERTY` before relying on a UDF in an indexed computed column

---

## Exam Tips

> [!tip] Exam Tips
>
> - **Inline TVF is the preferred function type** — it's inlined by the optimizer
> - Scalar functions **prevent parallelism** when used in DML or large queries
> - Multi-statement TVFs have a fixed cardinality estimate (1 row) by default unless using deferred compilation (SQL 2019+)
> - `SCHEMABINDING` is required for a UDF to be used in an indexed computed column or indexed view
> - `CROSS APPLY` returns only matched rows (like INNER JOIN); `OUTER APPLY` returns all left rows (like LEFT JOIN)

---

## Key Takeaways

- Prefer inline TVFs over scalar functions for set-based operations
- `SCHEMABINDING` prevents accidental breakage from schema changes
- Scalar UDF inlining (SQL 2019+) can automatically optimize simple scalar functions
- MSTVFs cause cardinality estimation problems because the optimizer cannot see inside them
- `APPLY` (CROSS or OUTER) is the standard way to invoke a TVF per row of a driving table

---

## Practice Question

**Practice Question**

A query joining a Customers table with a multi-statement TVF on CustomerID runs slowly and shows a poor estimated row count in the execution plan. What is the PRIMARY cause?

A. Multi-statement TVFs always force a table scan on the base table
B. The optimizer cannot see inside multi-statement TVFs and uses a fixed row count estimate
C. Multi-statement TVFs cannot be joined — CROSS APPLY must be used instead
D. The TVF is missing a clustered index on its return table variable

> [!success]- Answer
> **B — The optimizer cannot see inside multi-statement TVFs and uses a fixed row count estimate**
>
> MSTVFs are a "black box" to the optimizer — it cannot see the SELECT logic inside and uses a fixed estimate (100 rows in SQL Server 2014–2016, 1 row in earlier versions). This causes cardinality misestimation and poor plan choices downstream. Consider rewriting as an inline TVF (ITVF) where possible. CROSS APPLY (C) is the correct join mechanism for TVFs but doesn't cause the row count issue.

---

## Related Topics

- [01-Views](./01-views.md)
- [03-Stored Procedures](./03-stored-procedures.md)
- [01-CTEs & Window Functions](../03-advanced-tsql/01-ctes-window-functions.md)

---

## Official Documentation

- [User-Defined Functions](https://learn.microsoft.com/en-us/sql/relational-databases/user-defined-functions/user-defined-functions)
- [Scalar UDF Inlining](https://learn.microsoft.com/en-us/sql/relational-databases/user-defined-functions/scalar-udf-inlining)

---

**[← Previous](./01-views.md) | [↑ Back to Section](./programmability-objects.md) | [Next →](./03-stored-procedures.md)**
