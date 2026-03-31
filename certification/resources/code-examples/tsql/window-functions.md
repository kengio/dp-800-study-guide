---
title: Window Function Patterns
type: code-examples
tags:
  - dp-800
  - tsql
  - code-examples
  - window-functions
---

# Window Function Patterns

Reusable T-SQL window function patterns for Azure SQL Database and Microsoft Fabric SQL analytics workloads.

## Ranking Functions

Ranking functions assign a numeric rank to each row within a partition. All four variants are commonly tested on DP-800.

```sql
-- Setup: Sales table used throughout this section
-- CREATE TABLE Sales (
--   SaleID     INT PRIMARY KEY,
--   SalesRep   NVARCHAR(100),
--   Region     NVARCHAR(50),
--   SaleAmount DECIMAL(10,2),
--   SaleDate   DATE
-- );

-- ROW_NUMBER: unique sequential integer per partition, no ties
-- Use when you need a guaranteed unique rank (e.g., deduplication)
SELECT
    SaleID,
    SalesRep,
    Region,
    SaleAmount,
    ROW_NUMBER() OVER (PARTITION BY Region ORDER BY SaleAmount DESC) AS RowNum
FROM Sales;

-- RANK: ties receive the same rank; the next rank skips (1,1,3)
-- Use when you want to acknowledge ties but still show gaps
SELECT
    SaleID,
    SalesRep,
    Region,
    SaleAmount,
    RANK() OVER (PARTITION BY Region ORDER BY SaleAmount DESC) AS Rnk
FROM Sales;

-- DENSE_RANK: ties receive the same rank; no gaps (1,1,2)
-- Use when you need consecutive ranks despite ties
SELECT
    SaleID,
    SalesRep,
    Region,
    SaleAmount,
    DENSE_RANK() OVER (PARTITION BY Region ORDER BY SaleAmount DESC) AS DenseRnk
FROM Sales;

-- NTILE(n): divides rows into n roughly equal buckets
-- Use for quartiles, deciles, or percentile bands
SELECT
    SaleID,
    SalesRep,
    SaleAmount,
    NTILE(4) OVER (ORDER BY SaleAmount DESC) AS Quartile  -- 1 = top 25%
FROM Sales;

-- All four ranking functions side by side for comparison
SELECT
    SaleID,
    SalesRep,
    Region,
    SaleAmount,
    ROW_NUMBER()  OVER (PARTITION BY Region ORDER BY SaleAmount DESC) AS RowNum,
    RANK()        OVER (PARTITION BY Region ORDER BY SaleAmount DESC) AS Rnk,
    DENSE_RANK()  OVER (PARTITION BY Region ORDER BY SaleAmount DESC) AS DenseRnk,
    NTILE(4)      OVER (PARTITION BY Region ORDER BY SaleAmount DESC) AS Quartile
FROM Sales
ORDER BY Region, SaleAmount DESC;
```

## Aggregate Window Functions

Aggregate functions used with OVER() compute values across a window without collapsing rows, unlike GROUP BY.

```sql
-- SUM OVER: running total (cumulative) ordered by date
SELECT
    SaleDate,
    SalesRep,
    SaleAmount,
    -- Cumulative sum resets per SalesRep partition
    SUM(SaleAmount) OVER (
        PARTITION BY SalesRep
        ORDER BY SaleDate
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) AS RunningTotal
FROM Sales;

-- AVG, COUNT, MIN, MAX — all support OVER()
SELECT
    SaleID,
    SalesRep,
    Region,
    SaleAmount,
    AVG(SaleAmount) OVER (PARTITION BY Region) AS RegionAvgSale,
    COUNT(*)        OVER (PARTITION BY Region) AS RegionSaleCount,
    MIN(SaleAmount) OVER (PARTITION BY Region) AS RegionMinSale,
    MAX(SaleAmount) OVER (PARTITION BY Region) AS RegionMaxSale
FROM Sales;

-- Partitioned aggregate: show each row alongside its department total
-- Common pattern in Fabric SQL analytics for contribution % calculations
SELECT
    s.SaleID,
    s.SalesRep,
    s.Region,
    s.SaleAmount,
    SUM(s.SaleAmount) OVER (PARTITION BY s.Region) AS RegionTotal,
    -- Percentage of regional total
    ROUND(
        100.0 * s.SaleAmount
        / SUM(s.SaleAmount) OVER (PARTITION BY s.Region),
        2
    ) AS PctOfRegion
FROM Sales AS s;

-- 3-row moving average (preceding + current + following)
SELECT
    SaleDate,
    SalesRep,
    SaleAmount,
    AVG(SaleAmount) OVER (
        PARTITION BY SalesRep
        ORDER BY SaleDate
        ROWS BETWEEN 1 PRECEDING AND 1 FOLLOWING  -- window of 3 rows
    ) AS MovingAvg3
FROM Sales;
```

## ROWS vs RANGE Framing

The frame clause controls which rows are included in the window relative to the current row.

```sql
-- ROWS: physical row offsets — precise, usually preferred
-- RANGE: logical value range based on ORDER BY expression — includes ties

-- Running total using ROWS (explicit frame, same as default with ORDER BY)
SELECT
    SaleDate,
    SaleAmount,
    SUM(SaleAmount) OVER (
        ORDER BY SaleDate
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) AS RunningTotal_ROWS
FROM Sales;

-- RANGE version — WARNING: includes all rows with the same SaleDate value
-- If multiple sales share a date, all are summed into each other's row
SELECT
    SaleDate,
    SaleAmount,
    SUM(SaleAmount) OVER (
        ORDER BY SaleDate
        RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) AS RunningTotal_RANGE  -- may differ from ROWS when ties exist
FROM Sales;

-- 5-row centered moving average (2 before + current + 2 after)
SELECT
    SaleDate,
    SaleAmount,
    AVG(SaleAmount) OVER (
        ORDER BY SaleDate
        ROWS BETWEEN 2 PRECEDING AND 2 FOLLOWING
    ) AS MovingAvg5
FROM Sales;

-- Reverse running total: sum from current row to end of partition
SELECT
    SaleDate,
    SalesRep,
    SaleAmount,
    SUM(SaleAmount) OVER (
        PARTITION BY SalesRep
        ORDER BY SaleDate
        ROWS BETWEEN CURRENT ROW AND UNBOUNDED FOLLOWING
    ) AS RemainingTotal
FROM Sales;

-- Frame boundary quick reference:
-- UNBOUNDED PRECEDING  = start of partition
-- N PRECEDING          = N rows before current
-- CURRENT ROW          = current row
-- N FOLLOWING          = N rows after current
-- UNBOUNDED FOLLOWING  = end of partition
```

## Offset Functions

Offset functions look backward or forward within the ordered partition to compare values across rows.

```sql
-- LAG: value from N rows before the current row
-- Default N=1; third arg is the default when no prior row exists
SELECT
    SaleDate,
    SalesRep,
    SaleAmount,
    LAG(SaleAmount, 1, 0) OVER (
        PARTITION BY SalesRep
        ORDER BY SaleDate
    ) AS PrevMonthSale,
    -- Month-over-month change
    SaleAmount - LAG(SaleAmount, 1, 0) OVER (
        PARTITION BY SalesRep
        ORDER BY SaleDate
    ) AS MoMChange
FROM Sales;

-- LEAD: value from N rows after the current row
SELECT
    SaleDate,
    SalesRep,
    SaleAmount,
    LEAD(SaleAmount, 1, NULL) OVER (
        PARTITION BY SalesRep
        ORDER BY SaleDate
    ) AS NextMonthSale
FROM Sales;

-- FIRST_VALUE: first value in the window frame
-- Useful to compare each row to the baseline/first period
SELECT
    SaleDate,
    SalesRep,
    SaleAmount,
    FIRST_VALUE(SaleAmount) OVER (
        PARTITION BY SalesRep
        ORDER BY SaleDate
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) AS FirstSale,
    -- Growth vs first sale
    SaleAmount - FIRST_VALUE(SaleAmount) OVER (
        PARTITION BY SalesRep
        ORDER BY SaleDate
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) AS GrowthFromFirst
FROM Sales;

-- LAST_VALUE: last value in the frame
-- IMPORTANT: default frame is RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
-- which means LAST_VALUE sees only up to the current row, not the partition end.
-- Always specify an explicit frame to get the true last value.
SELECT
    SaleDate,
    SalesRep,
    SaleAmount,
    LAST_VALUE(SaleAmount) OVER (
        PARTITION BY SalesRep
        ORDER BY SaleDate
        ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING  -- explicit full frame
    ) AS LastSaleInPartition
FROM Sales;

-- Practical: find the previous order date for each customer
SELECT
    o.OrderID,
    o.CustomerID,
    o.OrderDate,
    LAG(o.OrderDate) OVER (
        PARTITION BY o.CustomerID
        ORDER BY o.OrderDate
    ) AS PrevOrderDate,
    DATEDIFF(DAY,
        LAG(o.OrderDate) OVER (PARTITION BY o.CustomerID ORDER BY o.OrderDate),
        o.OrderDate
    ) AS DaysSincePrevOrder
FROM Orders AS o;
```

## Distribution Functions

Distribution functions compute statistical position of each row within its partition.

```sql
-- PERCENT_RANK: relative rank as a value between 0 and 1
-- Formula: (rank - 1) / (total rows - 1)
-- First row = 0.0, last row = 1.0
SELECT
    SalesRep,
    SaleAmount,
    PERCENT_RANK() OVER (ORDER BY SaleAmount) AS PctRank
FROM Sales;

-- CUME_DIST: cumulative distribution
-- Formula: number of rows with value <= current / total rows
-- Always > 0; last row = 1.0
SELECT
    SalesRep,
    SaleAmount,
    CUME_DIST() OVER (ORDER BY SaleAmount) AS CumeDist
FROM Sales;

-- PERCENTILE_CONT: interpolated median (may not be an actual data value)
-- Uses WITHIN GROUP — not a standard OVER() window function
SELECT DISTINCT
    Region,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY SaleAmount)
        OVER (PARTITION BY Region) AS MedianSale_Interpolated
FROM Sales;

-- PERCENTILE_DISC: discrete median (returns an actual value from the dataset)
SELECT DISTINCT
    Region,
    PERCENTILE_DISC(0.5) WITHIN GROUP (ORDER BY SaleAmount)
        OVER (PARTITION BY Region) AS MedianSale_Discrete
FROM Sales;

-- Both together for comparison
SELECT DISTINCT
    Region,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY SaleAmount)
        OVER (PARTITION BY Region) AS MedianCont,
    PERCENTILE_DISC(0.5) WITHIN GROUP (ORDER BY SaleAmount)
        OVER (PARTITION BY Region) AS MedianDisc
FROM Sales
ORDER BY Region;
```

## Deduplication with ROW\_NUMBER

A classic pattern in Azure SQL and Fabric SQL for removing duplicate rows while keeping the most recent record.

```sql
-- Scenario: Customers table has duplicate rows per Email; keep the latest by CreatedDate

-- Step 1: Preview which rows would be removed (SELECT version)
WITH DeduplicatedCustomers AS (
    SELECT
        CustomerID,
        Email,
        FullName,
        CreatedDate,
        ROW_NUMBER() OVER (
            PARTITION BY Email          -- group duplicates by natural key
            ORDER BY CreatedDate DESC   -- most recent gets rn = 1
        ) AS rn
    FROM Customers
)
SELECT *
FROM DeduplicatedCustomers
WHERE rn > 1;  -- these are the duplicates that would be deleted

-- Step 2: DELETE duplicate rows (keep rn = 1 only)
WITH DeduplicatedCustomers AS (
    SELECT
        CustomerID,
        ROW_NUMBER() OVER (
            PARTITION BY Email
            ORDER BY CreatedDate DESC
        ) AS rn
    FROM Customers
)
DELETE FROM DeduplicatedCustomers
WHERE rn > 1;

-- Alternative: deduplicate into a new table (safer for large datasets)
SELECT CustomerID, Email, FullName, CreatedDate
INTO Customers_Clean
FROM (
    SELECT
        CustomerID,
        Email,
        FullName,
        CreatedDate,
        ROW_NUMBER() OVER (
            PARTITION BY Email
            ORDER BY CreatedDate DESC
        ) AS rn
    FROM Customers
) AS Ranked
WHERE rn = 1;
```

## Top-N Per Group

A frequently tested pattern: return the top N rows per category without using a correlated subquery.

```sql
-- Scenario: Top 3 products per Category by total revenue

-- CTE + ROW_NUMBER approach (most common, works in all Azure SQL tiers)
WITH RankedProducts AS (
    SELECT
        p.ProductID,
        p.ProductName,
        p.Category,
        SUM(oi.Quantity * oi.UnitPrice) AS TotalRevenue,
        ROW_NUMBER() OVER (
            PARTITION BY p.Category
            ORDER BY SUM(oi.Quantity * oi.UnitPrice) DESC
        ) AS rn
    FROM Products AS p
    INNER JOIN OrderItems AS oi ON oi.ProductID = p.ProductID
    GROUP BY p.ProductID, p.ProductName, p.Category
)
SELECT
    ProductID,
    ProductName,
    Category,
    TotalRevenue
FROM RankedProducts
WHERE rn <= 3
ORDER BY Category, TotalRevenue DESC;

-- Alternative: CROSS APPLY with TOP
-- Useful when the base table is large and Categories is a small dimension table
SELECT
    c.Category,
    t.ProductID,
    t.ProductName,
    t.TotalRevenue
FROM (SELECT DISTINCT Category FROM Products) AS c
CROSS APPLY (
    SELECT TOP 3
        p.ProductID,
        p.ProductName,
        SUM(oi.Quantity * oi.UnitPrice) AS TotalRevenue
    FROM Products AS p
    INNER JOIN OrderItems AS oi ON oi.ProductID = p.ProductID
    WHERE p.Category = c.Category
    GROUP BY p.ProductID, p.ProductName
    ORDER BY TotalRevenue DESC
) AS t
ORDER BY c.Category, t.TotalRevenue DESC;

-- Use RANK() instead of ROW_NUMBER() when ties should both appear
-- e.g., two products tied for 3rd place both show up in top-3
WITH RankedProducts AS (
    SELECT
        p.ProductID,
        p.ProductName,
        p.Category,
        SUM(oi.Quantity * oi.UnitPrice) AS TotalRevenue,
        RANK() OVER (
            PARTITION BY p.Category
            ORDER BY SUM(oi.Quantity * oi.UnitPrice) DESC
        ) AS rnk
    FROM Products AS p
    INNER JOIN OrderItems AS oi ON oi.ProductID = p.ProductID
    GROUP BY p.ProductID, p.ProductName, p.Category
)
SELECT ProductID, ProductName, Category, TotalRevenue
FROM RankedProducts
WHERE rnk <= 3
ORDER BY Category, TotalRevenue DESC;
```

---

**[← Back to Code Examples](./README.md) | [↑ Back to Certification](../../../README.md)**
