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

## WITH SCHEMABINDING

`SCHEMABINDING` binds the view to its underlying tables — preventing schema changes that would break the view and required for indexed views.

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
- Cannot DROP or ALTER underlying tables/columns referenced by the view
- Must use two-part names (`dbo.TableName`) — no `SELECT *`

## Indexed Views (Materialized Views)

Indexed views persist the result set to disk, making them useful for frequently queried aggregations.

```sql
-- Step 1: Create schema-bound view
CREATE VIEW dbo.vw_SalesByProduct
WITH SCHEMABINDING AS
SELECT
    ProductId,
    COUNT_BIG(*)         AS SaleCount,
    SUM(Amount)          AS TotalRevenue,
    SUM(Quantity)        AS TotalQuantity
FROM dbo.Sales
GROUP BY ProductId;
GO

-- Step 2: Create unique clustered index (materializes the view)
CREATE UNIQUE CLUSTERED INDEX UIX_vw_SalesByProduct
ON dbo.vw_SalesByProduct (ProductId);
```

**Requirements for indexed views:**
- `WITH SCHEMABINDING` is mandatory
- First index must be `UNIQUE CLUSTERED`
- Deterministic functions only
- No `OUTER JOIN`, `HAVING`, subqueries, `DISTINCT`, `TOP`, `UNION`
- `COUNT_BIG(*)` required when using `GROUP BY`

**Query optimizer behavior:**
- Enterprise Edition: optimizer automatically uses indexed views when beneficial
- Other editions: use `WITH (NOEXPAND)` hint to force indexed view usage

```sql
SELECT ProductId, TotalRevenue
FROM dbo.vw_SalesByProduct WITH (NOEXPAND)
WHERE ProductId = 42;
```

## Updatable Views

Simple views (single table, no aggregation, no DISTINCT) support INSERT/UPDATE/DELETE:

```sql
-- This view is updatable
CREATE VIEW dbo.vw_ActiveProducts AS
SELECT ProductId, Name, Price
FROM dbo.Products
WHERE IsActive = 1;

-- UPDATE through the view
UPDATE dbo.vw_ActiveProducts SET Price = 19.99 WHERE ProductId = 5;
```

Use `INSTEAD OF` triggers on views for complex update logic.

## Use Cases

- **Security**: Expose only certain columns/rows to users without table access
- **Simplification**: Encapsulate complex joins for reuse across queries
- **Indexed views**: Pre-compute aggregations for reporting dashboards

## Common Issues & Errors

| Issue | Cause | Resolution |
| :--- | :--- | :--- |
| Cannot drop table | View uses `SCHEMABINDING` | Drop the view first, or use `ALTER VIEW` to remove schemabinding |
| Indexed view not used | Not Enterprise, no `NOEXPAND` | Add `WITH (NOEXPAND)` hint |
| View returns stale data | Underlying table changed | Views are always live (except indexed views) — check base tables |

## Exam Tips

- Indexed views require `WITH SCHEMABINDING` and a `UNIQUE CLUSTERED` index as the first index
- `COUNT_BIG(*)` is required in grouped indexed views — `COUNT(*)` is not allowed
- On non-Enterprise editions, use `WITH (NOEXPAND)` to force the optimizer to use the indexed view

## Key Takeaways

- Views are virtual — no data stored (unless indexed)
- `SCHEMABINDING` prevents accidental schema changes and enables indexing
- Indexed views materialize query results and can dramatically speed up aggregation queries

## Related Topics

- [02-Functions](./02-functions.md)
- [03-Stored Procedures](./03-stored-procedures.md)

## Official Documentation

- [Views (SQL Server)](https://learn.microsoft.com/en-us/sql/relational-databases/views/views)
- [Create Indexed Views](https://learn.microsoft.com/en-us/sql/relational-databases/views/create-indexed-views)

---

**[↑ Back to Section](./README.md) | [Next →](./02-functions.md)**
