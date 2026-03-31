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

> [!abstract]
> - Covers CTEs (non-recursive and recursive), window functions (ROW_NUMBER, RANK, DENSE_RANK, LAG, LEAD, SUM OVER), and frame clauses
> - CTEs improve readability; recursive CTEs traverse hierarchies; window functions compute across related rows without collapsing them
> - Key exam topics: tie-breaking behavior of ranking functions, recursive CTE structure, ROWS vs RANGE frame

> [!tip] What the Exam Tests
> - Tie behavior: `ROW_NUMBER` = unique (arbitrary tiebreak); `RANK` = gaps after tie (1,1,3); `DENSE_RANK` = no gaps (1,1,2)
> - Recursive CTE: **anchor member** (runs once) `UNION ALL` **recursive member** (runs until no rows). Must have `MAXRECURSION` to prevent infinite loop
> - `ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW` = running total; `RANGE` uses logical range (can include ties)

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

## CTE Non-Materialization Behavior

CTEs are **not materialized** by default — they are expanded inline like a view. The optimizer may execute the CTE multiple times if it is referenced more than once in the same query. This is different from temp tables and table variables, which are physically materialized.

Recursive CTEs are an exception: the anchor result is temporarily cached for the recursive iterations.

```sql
-- CTE referenced twice — may execute twice (no materialization guarantee)
WITH ExpensiveCTE AS (
    SELECT CustomerID, COUNT(*) AS OrderCount
    FROM Orders
    GROUP BY CustomerID
)
SELECT c.Name, e.OrderCount
FROM Customers c
JOIN ExpensiveCTE e ON c.CustomerID = e.CustomerID
WHERE e.OrderCount > (SELECT AVG(OrderCount) FROM ExpensiveCTE);  -- CTE runs again!

-- Better: use temp table when CTE is referenced multiple times
SELECT CustomerID, COUNT(*) AS OrderCount
INTO #OrderCounts FROM Orders GROUP BY CustomerID;

SELECT c.Name, o.OrderCount FROM Customers c
JOIN #OrderCounts o ON c.CustomerID = o.CustomerID
WHERE o.OrderCount > (SELECT AVG(OrderCount) FROM #OrderCounts);
```

**When to prefer a temp table over a CTE:**

- CTE is referenced more than once with expensive aggregation/joins
- Statistics are needed on the intermediate result (optimizer can use temp table stats)

## Recursive CTE Depth Limit

The default maximum recursion depth is **100**. Use `OPTION(MAXRECURSION n)` to override; `0` means unlimited (use with caution — infinite loops will run until cancelled).

Always include an explicit termination condition in the recursive member to avoid runaway queries.

```sql
-- Traverse org chart with depth limit
WITH OrgHierarchy AS (
    -- Anchor: top-level managers
    SELECT EmployeeID, Name, ManagerID, 0 AS Level
    FROM Employees WHERE ManagerID IS NULL

    UNION ALL

    -- Recursive: employees reporting to previous level
    SELECT e.EmployeeID, e.Name, e.ManagerID, h.Level + 1
    FROM Employees e
    JOIN OrgHierarchy h ON e.ManagerID = h.EmployeeID
)
SELECT * FROM OrgHierarchy
ORDER BY Level, Name
OPTION(MAXRECURSION 50);  -- Safety: limit to 50 levels
```

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

> [!warning] Common Mistake
> RANK and DENSE_RANK both handle ties, but only DENSE_RANK avoids gaps in the sequence. If a question says "assign sequential ranks with no gaps even when rows tie," the answer is DENSE_RANK, not RANK.

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

## PERCENT_RANK and CUME_DIST

Both functions produce a value between 0.0 and 1.0 and are useful for percentile-based analysis, salary banding, and outlier detection.

| Function | Formula | Range |
| :--- | :--- | :--- |
| `PERCENT_RANK()` | (rank - 1) / (total rows - 1) | 0.0 (lowest) to 1.0 (highest) |
| `CUME_DIST()` | rows with value ≤ current / total rows | 1/n (lowest) to 1.0 (highest) |

Key difference: `PERCENT_RANK` uses the row's rank position; `CUME_DIST` counts how many rows have a value less than or equal to the current row.

```sql
SELECT EmployeeID, Name, Salary,
       PERCENT_RANK() OVER (ORDER BY Salary) AS PctRank,
       CUME_DIST() OVER (ORDER BY Salary) AS CumeDist
FROM Employees;
-- PERCENT_RANK: 0.0 for lowest, 1.0 for highest
-- CUME_DIST: 1.0/n for lowest, always 1.0 for highest

-- Find employees in top 10% of salary
WITH RankedSalaries AS (
    SELECT EmployeeID, Name, Salary,
           PERCENT_RANK() OVER (ORDER BY Salary) AS PctRank
    FROM Employees
)
SELECT * FROM RankedSalaries WHERE PctRank >= 0.90;
```

## FIRST_VALUE and LAST_VALUE Pitfall

`FIRST_VALUE` works correctly with the default frame. `LAST_VALUE` does **not** — the default frame is `RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW`, which stops at the current row, so `LAST_VALUE` returns the current row's value rather than the partition's last.

This is a common exam trap. Always specify an explicit frame for `LAST_VALUE`.

```sql
SELECT OrderID, OrderDate, TotalAmount,
       FIRST_VALUE(TotalAmount) OVER (PARTITION BY CustomerID ORDER BY OrderDate) AS FirstOrderAmount,
       -- LAST_VALUE needs explicit frame!
       LAST_VALUE(TotalAmount) OVER (
           PARTITION BY CustomerID
           ORDER BY OrderDate
           ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
       ) AS LastOrderAmount
FROM Orders;
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
- **PERCENT_RANK / CUME_DIST**: Salary banding, top-N percent filtering, outlier detection

## Common Issues & Errors

| Issue | Cause | Resolution |
| :--- | :--- | :--- |
| Infinite recursion in CTE | Missing/incorrect termination condition | Add `WHERE` in recursive member; use `MAXRECURSION` |
| Wrong running total | Missing `ROWS UNBOUNDED PRECEDING` | Default frame is `RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW` — can cause unexpected results with ties |
| `LAST_VALUE` returns current row | Default frame ends at current row | Add `ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING` |
| CTE runs slower when referenced twice | No materialization; query runs CTE logic multiple times | Replace with `#temp table` to force materialization |

## Best Practices

- Use temp tables instead of CTEs when the same CTE is referenced more than once in a query with expensive logic.
- Always specify `ROWS` (not `RANGE`) in window frame clauses to avoid unexpected tie behavior.
- Always include a termination condition in recursive CTEs and set an explicit `MAXRECURSION` limit appropriate to your data depth.
- Prefer `DENSE_RANK()` over `RANK()` when gaps in rank values would confuse downstream logic.
- Add `ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING` whenever using `LAST_VALUE` to get the true last value in the partition.

## Exam Tips

- `RANK()` leaves gaps after ties; `DENSE_RANK()` does not; `ROW_NUMBER()` has no ties
- Default window frame is `RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW` — be explicit with `ROWS`
- Recursive CTEs need both an anchor member and a recursive member joined with `UNION ALL`
- CTEs are **not materialized** — referencing a CTE twice may execute the underlying query twice
- `LAST_VALUE` with default frame returns the current row's value, not the partition's last value
- `PERCENT_RANK` returns 0.0 for the lowest row; `CUME_DIST` never returns 0.0
- `OPTION(MAXRECURSION 0)` removes the recursion limit — dangerous on unbounded hierarchies

## Key Takeaways

- CTEs improve readability — they don't inherently improve performance
- Window functions calculate over a window without reducing row count
- `PARTITION BY` in window functions is independent of `GROUP BY`
- CTE non-materialization is a performance trap when the same CTE is referenced multiple times

## Practice Questions

**Practice Question**

A CTE is referenced twice in the same query and contains a complex aggregation. The query runs slower than expected. What is the MOST LIKELY cause?

A. CTEs cannot contain aggregation functions
B. The CTE is executed twice because CTEs are not materialized
C. Window functions inside CTEs disable parallel execution
D. CTEs are limited to 100 rows by default

> [!success]- Answer
> **B — The CTE is executed twice because CTEs are not materialized**
>
> SQL Server CTEs are expanded inline — they are not cached or materialized like temp tables. When a CTE is referenced multiple times in the same query, the underlying logic may execute multiple times. For expensive CTEs referenced more than once, use a `#temp table` or table variable to materialize the results first. Option D is wrong (MAXRECURSION 100 only applies to recursive CTEs).

## Related Topics

- [02-JSON Functions](./02-json-functions.md)
- [05-Correlated Queries & Error Handling](./05-correlated-queries-error-handling.md)

## Official Documentation

- [WITH common_table_expression (Transact-SQL)](https://learn.microsoft.com/en-us/sql/t-sql/queries/with-common-table-expression-transact-sql)
- [Window Functions (Transact-SQL)](https://learn.microsoft.com/en-us/sql/t-sql/queries/select-over-clause-transact-sql)

---

**[↑ Back to Section](./README.md) | [Next →](./02-json-functions.md)**
