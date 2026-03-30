---
title: CTEs and Window Functions
type: study-material
tags:
  - dp-800
  - cte
  - window-functions
  - ranking
  - analytics
---

# CTEs and Window Functions

## Overview

Common Table Expressions (CTEs) provide named temporary result sets for readable, reusable queries. Window functions perform calculations across sets of rows related to the current row — without collapsing results like GROUP BY does.

## Common Table Expressions (CTEs)

### Basic CTE

```sql
-- Single CTE
WITH RecentOrders AS (
    SELECT OrderId, CustomerId, OrderDate, TotalAmount
    FROM dbo.Orders
    WHERE OrderDate >= DATEADD(DAY, -30, GETUTCDATE())
)
SELECT c.Name, r.OrderId, r.TotalAmount
FROM RecentOrders r
JOIN dbo.Customers c ON c.CustomerId = r.CustomerId;
```

### Multiple CTEs

```sql
WITH
TopCustomers AS (
    SELECT CustomerId, SUM(TotalAmount) AS Revenue
    FROM dbo.Orders
    GROUP BY CustomerId
    HAVING SUM(TotalAmount) > 10000
),
CustomerDetails AS (
    SELECT c.CustomerId, c.Name, c.Email
    FROM dbo.Customers c
    WHERE c.IsActive = 1
)
SELECT cd.Name, cd.Email, tc.Revenue
FROM TopCustomers tc
JOIN CustomerDetails cd ON cd.CustomerId = tc.CustomerId
ORDER BY tc.Revenue DESC;
```

### Recursive CTE

Recursive CTEs process hierarchical or graph data (org charts, bill of materials).

```sql
WITH EmployeeHierarchy AS (
    -- Anchor: top-level employees (no manager)
    SELECT EmployeeId, Name, ManagerId, 0 AS Level
    FROM dbo.Employees
    WHERE ManagerId IS NULL

    UNION ALL

    -- Recursive: employees at each level
    SELECT e.EmployeeId, e.Name, e.ManagerId, h.Level + 1
    FROM dbo.Employees e
    JOIN EmployeeHierarchy h ON h.EmployeeId = e.ManagerId
)
SELECT EmployeeId, Name, Level,
       REPLICATE('  ', Level) + Name AS IndentedName
FROM EmployeeHierarchy
ORDER BY Level, Name;
```

**Recursive CTE safeguards:**
- Default recursion limit: 100 (override with `OPTION (MAXRECURSION n)`)
- Always include a WHERE clause to terminate recursion

## Window Functions

Window functions use the `OVER()` clause to define the window of rows they operate on — the current row is never removed from the result.

### Ranking Functions

```sql
SELECT
    ProductId,
    CategoryId,
    Price,
    -- Global ranking (gaps after ties)
    RANK()          OVER (ORDER BY Price DESC) AS GlobalRank,
    -- No gaps after ties
    DENSE_RANK()    OVER (ORDER BY Price DESC) AS DenseRank,
    -- Unique sequential (no ties)
    ROW_NUMBER()    OVER (ORDER BY Price DESC, ProductId) AS RowNum,
    -- Divide into N buckets
    NTILE(4)        OVER (ORDER BY Price DESC) AS Quartile,
    -- Ranking within each category
    RANK()          OVER (PARTITION BY CategoryId ORDER BY Price DESC) AS CategoryRank
FROM dbo.Products;
```

### Aggregate Window Functions

```sql
SELECT
    OrderId,
    CustomerId,
    OrderDate,
    TotalAmount,
    -- Running total
    SUM(TotalAmount) OVER (
        PARTITION BY CustomerId
        ORDER BY OrderDate
        ROWS UNBOUNDED PRECEDING
    ) AS RunningTotal,
    -- Moving average (last 3 orders)
    AVG(TotalAmount) OVER (
        PARTITION BY CustomerId
        ORDER BY OrderDate
        ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
    ) AS MovingAvg3,
    -- Percentage of total
    TotalAmount / SUM(TotalAmount) OVER (PARTITION BY CustomerId) * 100 AS PctOfCustomerTotal
FROM dbo.Orders;
```

### Offset Functions

```sql
SELECT
    OrderId,
    CustomerId,
    OrderDate,
    TotalAmount,
    -- Previous row's value
    LAG(TotalAmount, 1, 0) OVER (PARTITION BY CustomerId ORDER BY OrderDate) AS PrevAmount,
    -- Next row's value
    LEAD(TotalAmount, 1, 0) OVER (PARTITION BY CustomerId ORDER BY OrderDate) AS NextAmount,
    -- First value in window
    FIRST_VALUE(TotalAmount) OVER (PARTITION BY CustomerId ORDER BY OrderDate
        ROWS UNBOUNDED PRECEDING) AS FirstOrderAmount,
    -- Last value in window
    LAST_VALUE(TotalAmount) OVER (PARTITION BY CustomerId ORDER BY OrderDate
        ROWS BETWEEN CURRENT ROW AND UNBOUNDED FOLLOWING) AS LastOrderAmount
FROM dbo.Orders;
```

### Frame Specification

```sql
-- ROWS vs RANGE:
-- ROWS: physical rows relative to current row
-- RANGE: logical rows with same ORDER BY value (can include ties)

OVER (ORDER BY Date ROWS UNBOUNDED PRECEDING)           -- all prior rows
OVER (ORDER BY Date ROWS BETWEEN 1 PRECEDING AND 1 FOLLOWING)  -- ±1 row
OVER (ORDER BY Date ROWS BETWEEN CURRENT ROW AND UNBOUNDED FOLLOWING) -- current to end
OVER (PARTITION BY Dept ORDER BY Salary)                -- partition only
```

## Common Patterns

```sql
-- Deduplicate: keep the most recent row per customer
WITH Ranked AS (
    SELECT *, ROW_NUMBER() OVER (PARTITION BY CustomerId ORDER BY UpdatedAt DESC) AS rn
    FROM dbo.CustomerEvents
)
DELETE FROM Ranked WHERE rn > 1;

-- Top N per group
WITH Ranked AS (
    SELECT *, DENSE_RANK() OVER (PARTITION BY CategoryId ORDER BY Sales DESC) AS dr
    FROM dbo.Products
)
SELECT * FROM Ranked WHERE dr <= 3;
```

## Use Cases

- **CTEs**: Break complex queries into readable named steps; recursive hierarchies
- **ROW_NUMBER**: Deduplication, pagination (`WHERE rn BETWEEN 1 AND 20`)
- **LAG/LEAD**: Period-over-period comparisons, detecting gaps in sequences
- **Running totals**: Cumulative sums for financial reporting

## Common Issues & Errors

| Issue | Cause | Resolution |
| :--- | :--- | :--- |
| Infinite recursion in CTE | Missing/incorrect termination condition | Add `WHERE` in recursive member; use `MAXRECURSION` |
| Wrong running total | Missing `ROWS UNBOUNDED PRECEDING` | Default frame is `RANGE UNBOUNDED PRECEDING` — can cause unexpected results with ties |
| `LAST_VALUE` returns current row | Default frame ends at current row | Add `ROWS BETWEEN CURRENT ROW AND UNBOUNDED FOLLOWING` |

## Exam Tips

- `RANK()` leaves gaps after ties; `DENSE_RANK()` does not; `ROW_NUMBER()` has no ties
- Default window frame is `RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW` — be explicit with `ROWS`
- Recursive CTEs need both an anchor member and a recursive member joined with `UNION ALL`

## Key Takeaways

- CTEs improve readability — they don't inherently improve performance
- Window functions calculate over a window without reducing row count
- `PARTITION BY` in window functions is independent of `GROUP BY`

## Related Topics

- [02-JSON Functions](./02-json-functions.md)
- [05-Correlated Queries & Error Handling](./05-correlated-queries-error-handling.md)

## Official Documentation

- [WITH common_table_expression (Transact-SQL)](https://learn.microsoft.com/en-us/sql/t-sql/queries/with-common-table-expression-transact-sql)
- [Window Functions (Transact-SQL)](https://learn.microsoft.com/en-us/sql/t-sql/queries/select-over-clause-transact-sql)

---

**[↑ Back to Section](./README.md) | [Next →](./02-json-functions.md)**
