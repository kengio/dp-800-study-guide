---
title: Views
type: study-material
tags:
  - dp-800
  - views
  - indexed-views
  - schema-binding
---

# Views

## Overview

Views are stored SELECT statements that act as virtual tables. SQL Server supports standard views, schema-bound views, and indexed (materialized) views — each with different performance and maintenance characteristics.

> [!abstract]
> - Covers standard views, indexed views, and updatable views
> - Views are virtual tables; indexed views materialize results with a unique clustered index
> - Key exam topics: indexed view requirements (SCHEMABINDING + UNIQUE CLUSTERED INDEX), updatable view rules, WITH CHECK OPTION

> [!tip] What the Exam Tests
> - Indexed views require `WITH SCHEMABINDING` on the view AND a `UNIQUE CLUSTERED INDEX` on it — both are mandatory
> - `WITH CHECK OPTION` ensures INSERT/UPDATE through a view stays within the view's WHERE clause filter
> - Non-deterministic functions (GETDATE, NEWID) are forbidden in indexed views

## Creating Views

```sql
-- Standard view
CREATE VIEW dbo.vw_ActiveCustomers AS
SELECT CustomerId, Name, Email, CreatedAt
FROM dbo.Customers
WHERE IsActive = 1;

-- View with multiple tables
CREATE VIEW dbo.vw_OrderSummary AS
SELECT
    o.OrderId,
    c.Name       AS CustomerName,
    o.OrderDate,
    SUM(oi.Quantity * oi.UnitPrice) AS TotalAmount
FROM dbo.Orders o
JOIN dbo.Customers c ON c.CustomerId = o.CustomerId
JOIN dbo.OrderItems oi ON oi.OrderId = o.OrderId
GROUP BY o.OrderId, c.Name, o.OrderDate;
```

## Schema Binding

`WITH SCHEMABINDING` binds the view to its underlying tables, preventing schema changes that would break the view. It is required for indexed views.

```sql
CREATE VIEW dbo.vw_ProductPricing
WITH SCHEMABINDING AS
SELECT
    p.ProductId,
    p.Name,
    p.Price,
    c.CategoryName
FROM dbo.Products p
JOIN dbo.Categories c ON c.CategoryId = p.CategoryId;
```

With `SCHEMABINDING`:

- Cannot DROP or ALTER underlying tables/columns referenced by the view while binding is active
- Must use two-part names (`dbo.TableName`) — `SELECT *` is not allowed
- Blocks `DROP TABLE` and column modifications on referenced objects
- Two-part naming (`dbo.TableName`) is required; unqualified names are rejected

> [!warning] Common Mistake
> You cannot create an indexed view without first creating the view WITH SCHEMABINDING. SCHEMABINDING prevents the underlying tables from being modified in ways that would break the view — it must come first.

## Indexed Views (Materialized Views)

An indexed view has a unique clustered index created on it, which physically stores the result set on disk. This makes it functionally equivalent to a materialized view in other database systems.

```sql
-- Create indexed view
CREATE VIEW dbo.vw_OrderSummary
WITH SCHEMABINDING
AS
SELECT CustomerID,
       COUNT_BIG(*) AS OrderCount,
       SUM(TotalAmount) AS TotalSpent
FROM dbo.Orders
GROUP BY CustomerID;
GO

-- Materialize the view
CREATE UNIQUE CLUSTERED INDEX IX_vw_OrderSummary
ON dbo.vw_OrderSummary(CustomerID);
```

**Requirements for indexed views:**

- `WITH SCHEMABINDING` is mandatory
- First index must be `UNIQUE CLUSTERED`
- Deterministic functions only (no `GETDATE()`, `NEWID()`, `RAND()`)
- No `OUTER JOIN`, `HAVING`, subqueries, CTEs, `DISTINCT`, `TOP`, or `UNION`
- `COUNT_BIG(*)` required when using `GROUP BY` — `COUNT(*)` is not allowed

**Query optimizer behavior:**

- Enterprise Edition: optimizer automatically uses indexed views when beneficial, even without a direct reference
- Other editions: use `WITH (NOEXPAND)` hint to force indexed view usage

```sql
SELECT ProductId, TotalRevenue
FROM dbo.vw_SalesByProduct WITH (NOEXPAND)
WHERE ProductId = 42;
```

## Updatable Views

Simple views (single base table, no aggregation, no `DISTINCT`, no `TOP`, no `ROWNUM`) support INSERT/UPDATE/DELETE against the underlying table.

```sql
CREATE VIEW dbo.vw_ActiveCustomers
AS
SELECT CustomerID, Name, Email
FROM Customers
WHERE IsActive = 1
WITH CHECK OPTION; -- Prevents inserting inactive customers via view
```

**Rules for DML through a view:**

- View must reference only a single base table
- No aggregate functions (`SUM`, `COUNT`, `AVG`, etc.)
- No `DISTINCT`, `TOP`, `GROUP BY`, or `HAVING`
- Columns being modified must map directly to base table columns

**WITH CHECK OPTION** ensures that any row inserted or updated through the view still satisfies the view's WHERE clause. Without it, you could insert a row that immediately disappears from the view.

**INSTEAD OF triggers** can make otherwise non-updatable views (multi-table joins, aggregations) accept DML by intercepting the operation and executing custom logic:

```sql
-- UPDATE through a simple updatable view
UPDATE dbo.vw_ActiveProducts SET Price = 19.99 WHERE ProductId = 5;
```

Use `INSTEAD OF` triggers on views for complex update logic involving multiple base tables.

## View Limitations

| Limitation | Detail |
|---|---|
| ORDER BY | Only allowed with TOP, OFFSET-FETCH, or FOR XML/JSON |
| Subqueries in FROM | Allowed in regular views; indexed views cannot use them |
| CTEs | Regular views can use CTEs; indexed views cannot |
| DISTINCT | Allowed in regular views; not in indexed views |
| Outer joins | Allowed in regular views; not in indexed views |
| System tables | Can be referenced; schema changes may silently break the view |

## Use Cases

- **Security**: Expose only certain columns/rows to users without table access
- **Simplification**: Encapsulate complex joins for reuse across queries
- **Indexed views**: Pre-compute aggregations for reporting dashboards
- **Updatable abstraction**: Expose a filtered subset of a table while enforcing constraints via `WITH CHECK OPTION`

## Common Issues & Errors

| Issue | Cause | Resolution |
| :--- | :--- | :--- |
| Cannot drop table | View uses `SCHEMABINDING` | Drop the view first, or use `ALTER VIEW` to remove schemabinding |
| Indexed view not used | Not Enterprise, no `NOEXPAND` | Add `WITH (NOEXPAND)` hint |
| View returns stale data | Underlying table changed | Views are always live (except indexed views) — check base tables |
| Index creation fails | Non-deterministic function in view | Replace `GETDATE()`, `NEWID()`, etc. with deterministic alternatives |
| DML through view fails | View spans multiple tables or has aggregation | Use `INSTEAD OF` trigger or target base table directly |

## Best Practices

- Always use `WITH SCHEMABINDING` for views that will be indexed or used in critical production queries to prevent accidental schema drift.
- Use `WITH CHECK OPTION` on filtered views to enforce data integrity when allowing DML through the view.
- Prefix view names with `vw_` or `v_` to distinguish them from base tables in queries and object browsers.
- Avoid `SELECT *` in view definitions — explicitly list columns so that adding columns to the base table does not silently change the view's output.
- For non-Enterprise editions, always add `WITH (NOEXPAND)` when querying indexed views to guarantee the materialized data is used.

## Exam Tips

- Indexed views require `WITH SCHEMABINDING` and a `UNIQUE CLUSTERED` index as the first index
- `COUNT_BIG(*)` is required in grouped indexed views — `COUNT(*)` is not allowed
- On non-Enterprise editions, use `WITH (NOEXPAND)` to force the optimizer to use the indexed view
- Non-deterministic functions (`GETDATE()`, `NEWID()`, `RAND()`) block index creation on a view
- `WITH CHECK OPTION` prevents DML that would cause rows to fall outside the view's filter — without it, "disappearing rows" can occur after insert/update

## Key Takeaways

- Views are virtual — no data stored (unless indexed)
- `SCHEMABINDING` prevents accidental schema changes and enables indexing
- Indexed views materialize query results and can dramatically speed up aggregation queries
- `WITH CHECK OPTION` enforces that DML through a view keeps rows visible through the same view

## Practice Questions

**Practice Question**

A developer creates a view with `WITH SCHEMABINDING` and tries to add a unique clustered index on it, but receives an error. Which condition is MOST likely causing the failure?

A. The view references a column with a non-deterministic function like GETDATE()
B. The view uses an INNER JOIN between two tables
C. The view's SELECT list includes the primary key column
D. The underlying table has a columnstore index

> [!success]- Answer
> **A — The view references a column with a non-deterministic function like GETDATE()**
>
> Indexed views require all functions to be deterministic (same output for same input). GETDATE(), NEWID(), RAND() are non-deterministic and prevent index creation. INNER JOINs (B) are allowed in indexed views. Including the PK (C) is fine. Columnstore indexes (D) on the base table do not affect view indexability.

## Related Topics

- [02-Functions](./02-functions.md)
- [03-Stored Procedures](./03-stored-procedures.md)

## Official Documentation

- [Views (SQL Server)](https://learn.microsoft.com/en-us/sql/relational-databases/views/views)
- [Create Indexed Views](https://learn.microsoft.com/en-us/sql/relational-databases/views/create-indexed-views)

---

**[↑ Back to Section](./README.md) | [Next →](./02-functions.md)**
