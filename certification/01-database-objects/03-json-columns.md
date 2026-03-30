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

## Use Cases

- **Product catalogs**: Variable attribute sets per product type stored as JSON
- **Event sourcing**: Event payloads with flexible schemas
- **API integration**: Store and query REST API responses directly in SQL
- **Configuration tables**: Application settings as structured JSON

## Common Issues & Errors

| Issue | Cause | Resolution |
| :--- | :--- | :--- |
| `JSON_VALUE` returns NULL | Path does not exist or value is not scalar | Use `JSON_QUERY` for objects/arrays; verify path |
| Slow JSON queries | No index on JSON property | Create computed column + index on the property |
| `ISJSON` returns 0 | Malformed JSON in the column | Add CHECK constraint on insert; validate at application layer |
| `OPENJSON` returns no rows | JSON is valid but path is wrong | Test path with `JSON_VALUE` first |

## Exam Tips

- `JSON_VALUE` returns scalars (strings); `JSON_QUERY` returns JSON objects or arrays
- `OPENJSON` with `WITH` clause provides typed output — preferred for structured parsing
- To filter efficiently on JSON properties, create a **computed column + index**
- `JSON_ARRAYAGG` and `JSON_CONTAINS` are newer functions — know which SQL Server version supports them

## Key Takeaways

- JSON is stored as `nvarchar` or the new native `json` type
- Always validate JSON with `ISJSON` or a `CHECK` constraint
- Index JSON properties via computed columns for query performance
- `FOR JSON PATH` converts relational results to JSON for API responses

## Related Topics

- [02-JSON Functions in Advanced T-SQL](../03-advanced-tsql/02-json-functions.md)
- [01-Tables & Indexes](./01-tables-indexes.md)

## Official Documentation

- [JSON Data in SQL Server](https://learn.microsoft.com/en-us/sql/relational-databases/json/json-data-sql-server)
- [OPENJSON (Transact-SQL)](https://learn.microsoft.com/en-us/sql/t-sql/functions/openjson-transact-sql)
- [FOR JSON (Transact-SQL)](https://learn.microsoft.com/en-us/sql/relational-databases/json/format-query-results-as-json-with-for-json-sql-server)

---

**[← Previous](./02-specialized-tables.md) | [↑ Back to Section](./README.md) | [Next →](./04-constraints-sequences.md)**
