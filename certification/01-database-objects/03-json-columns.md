---
title: JSON Columns and Indexes
type: study-material
tags:
  - dp-800
  - json
  - json-columns
  - indexes
---

# JSON Columns and Indexes

## Overview

SQL Server and Azure SQL store JSON data as `nvarchar` columns, but provide native JSON functions, path expressions, and (in newer versions) a dedicated `json` data type with JSON indexes for efficient semi-structured data handling.

> [!abstract]
> - Covers JSON storage in NVARCHAR columns, all JSON functions, OPENJSON, FOR JSON, and indexing strategies
> - JSON is not a native type — it is stored as NVARCHAR; validity checked with ISJSON()
> - Key exam topics: JSON_VALUE vs JSON_QUERY vs OPENJSON, lax vs strict path mode, computed column indexes

> [!tip] What the Exam Tests
> - `JSON_VALUE` returns a **scalar**; `JSON_QUERY` returns an **object or array fragment** — use JSON_QUERY when the path points to an object
> - `OPENJSON` without a WITH clause returns (key, value, type) rows; with a WITH clause returns typed columns
> - Lax mode (default): path errors return NULL. Strict mode: path errors throw an error

---

## Storing JSON Data

```sql
-- Traditional approach: store JSON in nvarchar column
CREATE TABLE dbo.Products (
    ProductId   int             NOT NULL PRIMARY KEY,
    Name        nvarchar(200)   NOT NULL,
    Attributes  nvarchar(max)   NULL  -- JSON stored here
    CHECK (ISJSON(Attributes) = 1)    -- Validate on insert/update
);

-- Modern approach (SQL Server 2025+ / Azure SQL): native json type
CREATE TABLE dbo.Events (
    EventId     int     NOT NULL PRIMARY KEY,
    Payload     json    NULL
);
```

---

## JSON Path Expressions

JSON path expressions use `$` for the root and dot/bracket notation:

```sql
-- $.property — access an object property
-- $[0] — access an array element
-- $.address.city — nested property
-- $.tags[0] — first element of array

DECLARE @json nvarchar(max) = N'{
    "name": "Widget",
    "price": 9.99,
    "tags": ["sale", "new"],
    "supplier": { "id": 5, "name": "Acme" }
}';

SELECT
    JSON_VALUE(@json, '$.name')               AS Name,
    JSON_VALUE(@json, '$.price')              AS Price,
    JSON_VALUE(@json, '$.tags[0]')            AS FirstTag,
    JSON_VALUE(@json, '$.supplier.name')      AS Supplier;
```

---

## Key JSON Functions

### Reading JSON

```sql
-- JSON_VALUE: scalar value (string output)
SELECT JSON_VALUE(Attributes, '$.color') FROM dbo.Products;

-- JSON_QUERY: returns a JSON fragment (object or array)
SELECT JSON_QUERY(Attributes, '$.dimensions') FROM dbo.Products;

-- OPENJSON: parses JSON into rows
SELECT *
FROM OPENJSON(@json)
WITH (
    name    nvarchar(200)   '$.name',
    price   decimal(10,2)  '$.price',
    tags    nvarchar(max)   '$.tags' AS JSON
);
```

> [!warning] Common Mistake
> `JSON_VALUE(col, '$.product.specs')` returns NULL when `specs` is an object — not an error, and not the object. Use `JSON_QUERY(col, '$.product.specs')` to extract objects or arrays.

### Building JSON

```sql
-- JSON_OBJECT: construct a JSON object
SELECT JSON_OBJECT('id': ProductId, 'name': Name) FROM dbo.Products;

-- JSON_ARRAY: construct a JSON array
SELECT JSON_ARRAY(1, 'two', NULL, GETDATE());

-- JSON_ARRAYAGG: aggregate rows into a JSON array (SQL 2022+)
SELECT JSON_ARRAYAGG(Name ORDER BY Name) FROM dbo.Products;

-- FOR JSON PATH: convert query results to JSON
SELECT ProductId, Name, Attributes
FROM dbo.Products
FOR JSON PATH, ROOT('products');
```

### Modifying JSON

```sql
-- JSON_MODIFY: update a value in a JSON string
UPDATE dbo.Products
SET Attributes = JSON_MODIFY(Attributes, '$.color', 'blue')
WHERE ProductId = 1;
```

### Filtering JSON

```sql
-- JSON_CONTAINS (SQL 2025+ / Azure SQL): check if JSON contains a value
SELECT * FROM dbo.Products
WHERE JSON_CONTAINS(Attributes, '"sale"', '$.tags') = 1;

-- Traditional approach using JSON_VALUE
SELECT * FROM dbo.Products
WHERE JSON_VALUE(Attributes, '$.color') = 'blue';
```

---

## JSON Indexes

To efficiently filter or sort on JSON properties, create a computed column and index it:

```sql
-- Create a computed column for the JSON property
ALTER TABLE dbo.Products
ADD Color AS JSON_VALUE(Attributes, '$.color');

-- Index the computed column
CREATE INDEX IX_Products_Color ON dbo.Products (Color);

-- Query now uses the index
SELECT * FROM dbo.Products WHERE Color = 'blue';
```

For the native `json` type, SQL Server supports JSON path indexes directly:

```sql
-- Native json type index (SQL Server 2025+ / Azure SQL)
CREATE INDEX IX_Events_UserId
ON dbo.Events (CAST(JSON_VALUE(Payload, '$.userId') AS int));
```

---

## JSON Computed Columns for Indexing

**Problem:** Using `JSON_VALUE` in a `WHERE` clause causes a table scan — the optimizer cannot index a JSON path expression directly.

**Solution:** Extract the JSON property into a **PERSISTED computed column**, then create an index on that column.

PERSISTED computed columns are physically stored on disk (unlike virtual computed columns), which is required for indexing.

```sql
-- Add persisted computed column extracting from JSON
ALTER TABLE Orders
ADD ShipCountry AS JSON_VALUE(ShippingJSON, '$.country') PERSISTED;

-- Index the computed column
CREATE INDEX IX_Orders_ShipCountry ON Orders(ShipCountry);

-- Query now uses the index (optimizer treats JSON_VALUE(...) as the computed column)
SELECT OrderID, TotalAmount
FROM Orders
WHERE JSON_VALUE(ShippingJSON, '$.country') = 'US';

-- Filtered index on computed column for sparse values
CREATE INDEX IX_Orders_UK_Country
ON Orders(ShipCountry, TotalAmount)
WHERE ShipCountry = 'UK';
```

---

## JSON_ARRAYAGG and JSON_OBJECTAGG

Available in SQL Server 2022 and Azure SQL, these aggregate functions build JSON output directly from rows without requiring `FOR JSON` workarounds.

- **JSON_ARRAYAGG**: aggregates a column of values into a JSON array (like `STRING_AGG` but produces JSON)
- **JSON_OBJECTAGG**: aggregates key-value row pairs into a single JSON object
- **Use case**: build nested JSON results inline within a query

```sql
-- JSON_ARRAYAGG: list of product names per category
SELECT CategoryID,
       JSON_ARRAYAGG(ProductName ORDER BY ProductName) AS ProductNames
FROM Products
GROUP BY CategoryID;

-- JSON_OBJECTAGG: build a property bag from rows
SELECT OrderID,
       JSON_OBJECTAGG(AttributeName: AttributeValue) AS Attributes
FROM OrderAttributes
GROUP BY OrderID;

-- Nested JSON: orders with line items aggregated
SELECT o.OrderID, o.OrderDate,
       JSON_ARRAYAGG(JSON_OBJECT(
           'sku': li.SKU,
           'qty': li.Quantity,
           'price': li.UnitPrice
       )) AS LineItems
FROM Orders o
JOIN LineItems li ON o.OrderID = li.OrderID
GROUP BY o.OrderID, o.OrderDate;
```

---

## Strict vs Lax Mode in JSON Paths

JSON path expressions support two modes that control how missing paths are handled.

- **Lax mode (default)**: missing paths return `NULL` instead of raising an error
- **Strict mode**: raises error 13608 if the specified path does not exist in the JSON
- **When to use strict**: data validation and ETL pipelines where a missing property indicates bad or incomplete data

```sql
DECLARE @json NVARCHAR(MAX) = '{"name":"Alice","address":{"city":"Seattle"}}';

-- Lax (default): missing path returns NULL
SELECT JSON_VALUE(@json, 'lax $.phone');         -- NULL, no error
SELECT JSON_VALUE(@json, '$.phone');              -- NULL (lax is default)

-- Strict: missing path raises error
SELECT JSON_VALUE(@json, 'strict $.phone');      -- Error 13608

-- Practical: validate required properties during import
INSERT INTO Customers (Name, City)
SELECT
    JSON_VALUE(j.JsonData, 'strict $.name'),   -- fails fast if name missing
    JSON_VALUE(j.JsonData, 'lax $.city')       -- OK if city missing
FROM StagingJSON j
WHERE IS_JSON(j.JsonData) = 1;
```

---

## JSON with OPENJSON and Schema Binding

The `OPENJSON` function with the `WITH` clause shreds JSON into typed relational rows. Use the `AS JSON` modifier in the `WITH` clause to preserve nested objects or arrays as JSON fragments for further processing.

```sql
DECLARE @orderJSON NVARCHAR(MAX) = '{
    "orderId": 1001,
    "customer": "Alice",
    "items": [{"sku":"A1","qty":2},{"sku":"B2","qty":1}]
}';

-- Parse top-level properties
SELECT * FROM OPENJSON(@orderJSON)
WITH (
    OrderId INT '$.orderId',
    Customer NVARCHAR(100) '$.customer',
    Items NVARCHAR(MAX) '$.items' AS JSON  -- AS JSON preserves the array
);

-- Shred nested array with CROSS APPLY
SELECT h.OrderId, li.SKU, li.Qty
FROM (SELECT 1001 AS OrderId, @orderJSON AS Doc) h
CROSS APPLY OPENJSON(h.Doc, '$.items')
WITH (SKU NVARCHAR(20) '$.sku', Qty INT '$.qty') li;
```

---

## Use Cases

- **Product catalogs**: Variable attribute sets per product type stored as JSON
- **Event sourcing**: Event payloads with flexible schemas
- **API integration**: Store and query REST API responses directly in SQL
- **Configuration tables**: Application settings as structured JSON

---

## Common Issues & Errors

| Issue | Cause | Resolution |
| :--- | :--- | :--- |
| `JSON_VALUE` returns NULL | Path does not exist or value is not scalar | ==Use `JSON_QUERY` for objects/arrays; verify path== |
| Slow JSON queries | No index on JSON property | Create PERSISTED computed column + index on the property |
| `ISJSON` returns 0 | Malformed JSON in the column | Add CHECK constraint on insert; validate at application layer |
| `OPENJSON` returns no rows | JSON is valid but path is wrong | Test path with `JSON_VALUE` first |
| Error 13608 | Strict mode path not found | Switch to lax mode or fix the JSON to include the required property |

---

## Best Practices

- Always add a `CHECK (ISJSON(col) = 1)` constraint on `nvarchar` columns that store JSON to reject malformed data at the database layer.
- Use PERSISTED computed columns — not virtual ones — when you need to index a JSON property; virtual computed columns cannot be indexed.
- Prefer `strict` mode in ETL and import pipelines to catch missing required properties early; use `lax` mode for optional fields.
- Use `JSON_ARRAYAGG` / `JSON_OBJECTAGG` (SQL Server 2022+) for aggregating JSON inline instead of post-processing `FOR JSON PATH` results.
- Shred JSON into relational columns at insert time when the data will be queried frequently; keep JSON for flexible or rarely queried attributes only.

---

## Exam Tips

> [!tip] Exam Tips
> - `JSON_VALUE` returns scalars (strings); `JSON_QUERY` returns JSON objects or arrays
> - `OPENJSON` with `WITH` clause provides typed output — preferred for structured parsing
> - To filter efficiently on JSON properties, create a **PERSISTED computed column + index**
> - `JSON_ARRAYAGG` and `JSON_CONTAINS` are newer functions — know which SQL Server version supports them
> - Lax mode is the default; strict mode raises error 13608 on missing paths
> - `AS JSON` in an `OPENJSON WITH` clause preserves nested arrays/objects as JSON strings

---

## Key Takeaways

- JSON is stored as `nvarchar` or the new native `json` type
- Always validate JSON with `ISJSON` or a `CHECK` constraint
- Index JSON properties via PERSISTED computed columns for query performance
- `FOR JSON PATH` converts relational results to JSON for API responses
- `JSON_ARRAYAGG` and `JSON_OBJECTAGG` (SQL Server 2022+) aggregate rows directly into JSON
- Strict vs lax mode controls whether missing JSON paths raise an error or return NULL

---

## Practice Question

A table has a JSON column `Metadata` and a query filters on `JSON_VALUE(Metadata, '$.region') = 'EU'`. The query is slow with a full table scan. What is the BEST solution?

A. Use FOR JSON PATH to reformat the data
B. Add a PERSISTED computed column on `JSON_VALUE(Metadata, '$.region')` and index it
C. Switch to OPENJSON for better performance
D. Enable JSON path strict mode

> [!success]- Answer
> **B — Add a PERSISTED computed column on `JSON_VALUE(Metadata, '$.region')` and index it**
>
> The optimizer cannot index a JSON path expression directly. A PERSISTED computed column materializes the extracted value, and an index on that column allows efficient seeks. OPENJSON (C) is for shredding arrays and doesn't help filter performance. Strict mode (D) changes error behavior, not query speed.

---

## Related Topics

- [02-JSON Functions in Advanced T-SQL](../03-advanced-tsql/02-json-functions.md)
- [01-Tables & Indexes](./01-tables-indexes.md)

---

## Official Documentation

- [JSON Data in SQL Server](https://learn.microsoft.com/en-us/sql/relational-databases/json/json-data-sql-server)
- [OPENJSON (Transact-SQL)](https://learn.microsoft.com/en-us/sql/t-sql/functions/openjson-transact-sql)
- [FOR JSON (Transact-SQL)](https://learn.microsoft.com/en-us/sql/relational-databases/json/format-query-results-as-json-with-for-json-sql-server)

---

**[← Previous](./02-specialized-tables.md) | [↑ Back to Section](./database-objects.md) | [Next →](./04-constraints-sequences.md)**
