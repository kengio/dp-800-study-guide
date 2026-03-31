---
title: JSON Functions
type: study-material
tags:
  - dp-800
  - json
  - json-functions
  - openjson
  - for-json
---

# JSON Functions

## Overview

SQL Server provides a comprehensive set of JSON functions for reading, constructing, modifying, and filtering JSON data. These are heavily tested in DP-800 given the exam's focus on semi-structured data and AI payloads.

> [!abstract]
> - Deep-dive into all T-SQL JSON functions: extraction, modification, parsing, and serialization
> - JSON is stored as NVARCHAR — all functions operate on string representations
> - Key exam topics: JSON_VALUE vs JSON_QUERY, OPENJSON WITH clause, FOR JSON PATH vs AUTO, lax vs strict

> [!tip] What the Exam Tests
> - `JSON_VALUE` = scalar value only; `JSON_QUERY` = object or array fragment; if path points to object, JSON_VALUE returns NULL
> - `OPENJSON` without WITH = generic (key/value/type rows); with WITH = typed columns matching JSON structure
> - `FOR JSON PATH` with dot-notation column aliases (`name AS 'product.name'`) creates nested JSON; `FOR JSON AUTO` infers from table aliases

---

## Reading JSON

### JSON_VALUE — Scalar Extraction

```sql
DECLARE @json nvarchar(max) = N'{
    "customer": {
        "id": 42,
        "name": "Alice",
        "tier": "gold"
    },
    "tags": ["vip", "loyal"],
    "score": 9.5
}';

SELECT
    JSON_VALUE(@json, '$.customer.id')     AS CustomerId,   -- '42'
    JSON_VALUE(@json, '$.customer.name')   AS Name,         -- 'Alice'
    JSON_VALUE(@json, '$.tags[0]')         AS FirstTag,     -- 'vip'
    JSON_VALUE(@json, '$.score')           AS Score;        -- '9.5'
-- Returns NULL if path not found (default: lax mode)
-- Returns error in strict mode: JSON_VALUE(@json, 'strict $.missing')
```

### JSON_QUERY — Object/Array Extraction

```sql
SELECT
    JSON_QUERY(@json, '$.customer')    AS CustomerObject,  -- full JSON object
    JSON_QUERY(@json, '$.tags')        AS TagsArray;       -- full JSON array
-- Returns NULL for scalar values (use JSON_VALUE for those)
```

> [!warning] Common Mistake
> `JSON_VALUE(col, '$.product.specs')` silently returns NULL when `specs` is an object — this is lax mode default behavior. In strict mode, it would throw an error. The exam often presents both behaviors as answer choices: know which is default (lax = NULL, not error).

### OPENJSON — Parse to Rows

```sql
-- Default: key-value pairs
SELECT [key], [value], [type]
FROM OPENJSON(@json, '$.customer');
-- Returns: id/42/2, name/Alice/1, tier/gold/1

-- Typed output with WITH
SELECT id, name, tier
FROM OPENJSON(@json, '$.customer')
WITH (
    id      int             '$.id',
    name    nvarchar(100)   '$.name',
    tier    nvarchar(20)    '$.tier'
);

-- Parse an array
SELECT value AS Tag
FROM OPENJSON(@json, '$.tags');
```

**OPENJSON type values:**

| Value | JSON Type |
| :--- | :--- |
| 0 | null |
| 1 | string |
| 2 | ==number== |
| 3 | true/false |
| 4 | array |
| 5 | object |

---

## Building JSON

### JSON_OBJECT

```sql
-- Build a JSON object
SELECT JSON_OBJECT(
    'id'   : CustomerId,
    'name' : Name,
    'email': Email
) AS CustomerJson
FROM dbo.Customers;
```

### JSON_ARRAY

```sql
-- Build a JSON array
SELECT JSON_ARRAY(1, 'two', NULL, GETDATE());
-- [1,"two",null,"2025-06-15T10:00:00"]
```

### JSON_ARRAYAGG (SQL Server 2022+)

```sql
-- Aggregate rows into a JSON array grouped by category
SELECT
    CategoryId,
    JSON_ARRAYAGG(Name ORDER BY Name) AS ProductNames
FROM dbo.Products
GROUP BY CategoryId;

-- Aggregate full JSON objects into an array
SELECT
    OrderId,
    JSON_ARRAYAGG(
        JSON_OBJECT('sku': Sku, 'qty': Quantity, 'price': UnitPrice)
        ORDER BY LineNumber
    ) AS LineItemsJson
FROM dbo.OrderLines
GROUP BY OrderId;
```

### JSON_OBJECTAGG (SQL Server 2022+)

```sql
-- Aggregate key-value pairs into a single JSON object
-- Useful for pivoting attribute tables into JSON documents
SELECT
    ProductId,
    JSON_OBJECTAGG(AttributeName: AttributeValue) AS Attributes
FROM dbo.ProductAttributes
GROUP BY ProductId;
-- Example output: {"color":"red","size":"L","weight":"1.2kg"}

-- Combine with JSON_OBJECTAGG for config tables
SELECT JSON_OBJECTAGG(ConfigKey: ConfigValue) AS AppConfig
FROM dbo.AppSettings
WHERE IsActive = 1;
-- Output: {"MaxRetries":"3","Timeout":"30","Environment":"prod"}
```

### FOR JSON PATH

```sql
-- Convert query results to JSON
SELECT
    c.CustomerId,
    c.Name,
    o.OrderId,
    o.TotalAmount
FROM dbo.Customers c
JOIN dbo.Orders o ON o.CustomerId = c.CustomerId
FOR JSON PATH, ROOT('customers');

-- Output:
-- {"customers":[{"CustomerId":1,"Name":"Alice","OrderId":101,"TotalAmount":99.99},...]}
```

### FOR JSON AUTO

```sql
-- Auto-nesting based on table aliases
SELECT c.Name, o.OrderId
FROM dbo.Customers c
JOIN dbo.Orders o ON o.CustomerId = c.CustomerId
FOR JSON AUTO;
-- Nests Orders under Customers automatically
```

---

## Modifying JSON

### JSON_MODIFY

```sql
DECLARE @json nvarchar(max) = N'{"name":"Alice","score":7}';

-- Update existing value
SET @json = JSON_MODIFY(@json, '$.score', 9.5);

-- Add new property
SET @json = JSON_MODIFY(@json, '$.tier', 'gold');

-- Delete property (set to NULL with explicit NULL cast)
SET @json = JSON_MODIFY(@json, '$.tier', NULL);

-- Append to array
SET @json = JSON_MODIFY(@json, 'append $.tags', 'vip');
```

---

## Filtering with JSON

### JSON_CONTAINS (SQL Server 2025+ / Azure SQL)

```sql
-- Check if an array contains a value
SELECT * FROM dbo.Products
WHERE JSON_CONTAINS(Tags, '"sale"') = 1;

-- Check nested path
SELECT * FROM dbo.Events
WHERE JSON_CONTAINS(Payload, '{"status":"active"}', '$.user') = 1;
```

### ISJSON — Validation

```sql
SELECT * FROM dbo.Products
WHERE ISJSON(Attributes) = 1;  -- 1 = valid JSON, 0 = invalid

-- ISJSON with type (SQL 2022+)
WHERE ISJSON(Attributes, OBJECT) = 1   -- must be a JSON object
WHERE ISJSON(Tags, ARRAY) = 1          -- must be a JSON array
```

---

## JSON Path Expressions Quick Reference

| Expression | Returns |
| :--- | :--- |
| `$.property` | Top-level property |
| `$.a.b` | Nested property |
| `$.array[0]` | First element of array |
| `$.array[*]` | All array elements (OPENJSON) |
| `lax $.missing` | ==NULL if missing (default)== |
| `strict $.missing` | Error if missing |

Path mode defaults to `lax` in all JSON functions. Prefix with `strict` to
convert missing-path NULLs into errors — useful for validation queries.

---

## Nested JSON with CROSS APPLY

Use `CROSS APPLY OPENJSON` to shred nested arrays within JSON documents into
a flat relational result set.

```sql
-- Order JSON with nested line items array
DECLARE @orders NVARCHAR(MAX) = '[
    {"id": 1, "customer": "Alice", "items": [{"sku":"A1","qty":2},{"sku":"B2","qty":1}]},
    {"id": 2, "customer": "Bob",   "items": [{"sku":"C3","qty":5}]}
]';

-- Shred orders, then shred each items array
SELECT o.id, o.customer, li.sku, li.qty
FROM OPENJSON(@orders)
WITH (
    id       INT             '$.id',
    customer NVARCHAR(100)   '$.customer',
    items    NVARCHAR(MAX)   '$.items' AS JSON
) o
CROSS APPLY OPENJSON(o.items)
WITH (sku NVARCHAR(20) '$.sku', qty INT '$.qty') li;
```

The `AS JSON` flag in the `WITH` clause tells OPENJSON to return the nested
array as a raw JSON fragment rather than a string, enabling the second
`CROSS APPLY OPENJSON` call on it.

---

## JSON Schema Validation Patterns

### IS_JSON as a CHECK Constraint

```sql
-- Enforce valid JSON at write time
ALTER TABLE Products
ADD CONSTRAINT CK_ValidJSON CHECK (IS_JSON(Attributes) = 1);
```

### ETL Validation — Detect Invalid or Incomplete Rows

```sql
-- Validate required JSON properties during bulk load
SELECT src.RowID, src.JsonData
FROM StagingTable src
WHERE IS_JSON(src.JsonData) = 0                              -- invalid JSON
   OR JSON_VALUE(src.JsonData, 'strict $.id')   IS NULL      -- missing required field
   OR JSON_VALUE(src.JsonData, 'strict $.name') IS NULL;

-- Count valid vs invalid JSON rows
SELECT
    SUM(CASE WHEN IS_JSON(JsonData) = 1 THEN 1 ELSE 0 END) AS ValidCount,
    SUM(CASE WHEN IS_JSON(JsonData) = 0 THEN 1 ELSE 0 END) AS InvalidCount
FROM StagingTable;
```

### Type-Specific Validation (SQL Server 2022+)

```sql
-- Reject rows where the column is not a JSON object (rejects arrays, scalars)
ALTER TABLE Events
ADD CONSTRAINT CK_PayloadIsObject CHECK (ISJSON(Payload, OBJECT) = 1);
```

---

## Practical Patterns

```sql
-- Expand JSON array column into rows
SELECT p.ProductId, t.Tag
FROM dbo.Products p
CROSS APPLY OPENJSON(p.Tags) WITH (Tag nvarchar(50) '$') AS t;

-- Build AI prompt payload as JSON
SELECT JSON_OBJECT(
    'model'     : 'gpt-4o',
    'messages'  : JSON_QUERY(JSON_ARRAY(
        JSON_OBJECT('role': 'system', 'content': 'You are a helpful assistant.'),
        JSON_OBJECT('role': 'user',   'content': @UserQuestion)
    ))
) AS RequestPayload;
```

---

## Use Cases

- **Storing flexible attributes**: Product metadata, event payloads, configuration
- **API response storage**: Cache raw API responses and query them with JSON functions
- **RAG pipelines**: Convert query results to JSON for LLM prompts using `FOR JSON`
- **Data exchange**: Import/export data in JSON format for microservices

---

## Common Issues & Errors

| Issue | Cause | Resolution |
| :--- | :--- | :--- |
| `JSON_VALUE` returns NULL | Path not found (lax mode) | ==Verify path; use `strict` to get an error instead== |
| `JSON_QUERY` returns NULL on scalar | Scalar values need `JSON_VALUE` | Use `JSON_VALUE` for strings/numbers, `JSON_QUERY` for objects/arrays |
| `FOR JSON` produces unexpected nesting | Column naming causes auto-nesting | Use explicit aliases or `FOR JSON PATH` with dot notation |
| `CROSS APPLY OPENJSON` returns no rows | Nested column not declared `AS JSON` | Add `AS JSON` flag to the nested array column in the outer `WITH` clause |
| `JSON_OBJECTAGG` / `JSON_ARRAYAGG` not found | Functions require SQL Server 2022+ | Verify compatibility level ≥ 160; use `FOR JSON` as fallback on older versions |

---

## Best Practices

- Store JSON columns as `NVARCHAR(MAX)` and add an `IS_JSON` CHECK constraint to catch invalid data at write time rather than at query time.
- Prefer `OPENJSON` with a typed `WITH` clause over repeated `JSON_VALUE` calls — it parses the document once and produces strongly-typed columns in a single pass.
- Use `strict` path mode in validation and ETL queries so missing required fields surface as errors rather than silent NULLs.
- Index computed columns derived from `JSON_VALUE` (e.g., `AS JSON_VALUE(Payload, '$.customerId')`) when the same JSON property appears frequently in `WHERE` or `JOIN` predicates.
- Prefer `JSON_OBJECTAGG` / `JSON_ARRAYAGG` (SQL 2022+) over `FOR JSON PATH` when aggregating subsets of rows — they compose cleanly inside larger `SELECT` statements without subqueries.

---

## Exam Tips

> [!tip] Exam Tips
> - `JSON_VALUE` = scalar → string; `JSON_QUERY` = objects/arrays → JSON fragment
> - `OPENJSON` with `WITH` clause provides strongly-typed output — preferred for structured parsing
> - `FOR JSON PATH` gives explicit control; `FOR JSON AUTO` infers nesting from aliases
> - `JSON_ARRAYAGG` and `JSON_OBJECTAGG` are SQL Server 2022+ — know them for newer platform questions
> - Default path mode is `lax` (returns NULL on missing path); `strict` raises an error — critical for exam scenario questions about error behavior

---

## Practice Questions

**Practice Question**

A query uses `JSON_VALUE(col, '$.address.city')` but some rows have no `address` property. What is returned for those rows by default?

A. An empty string ''
B. NULL
C. An error is raised
D. The string 'null'

> [!success]- Answer
> **B — NULL**
>
> JSON_VALUE uses lax mode by default. In lax mode, if the path doesn't exist or the value is JSON null, it returns SQL NULL — no error is raised. To raise an error for missing paths, use `JSON_VALUE(col, 'strict $.address.city')`. Note: JSON `null` (lowercase) maps to SQL NULL in JSON_VALUE.

---

## Key Takeaways

- Two read functions: `JSON_VALUE` (scalar) and `JSON_QUERY` (object/array)
- `OPENJSON` is the most versatile — converts JSON to relational rows
- `FOR JSON` converts relational results to JSON — essential for RAG prompt building
- `JSON_OBJECTAGG` / `JSON_ARRAYAGG` (SQL 2022+) aggregate rows directly into JSON without subqueries
- `CROSS APPLY OPENJSON` with `AS JSON` is the pattern for shredding nested arrays

---

## Related Topics

- [03-JSON Columns](../01-database-objects/03-json-columns.md)
- [02-RAG Prompts and Responses](../11-rag/02-prompts-and-responses.md)

---

## Official Documentation

- [JSON Functions (Transact-SQL)](https://learn.microsoft.com/en-us/sql/t-sql/functions/json-functions-transact-sql)
- [OPENJSON (Transact-SQL)](https://learn.microsoft.com/en-us/sql/t-sql/functions/openjson-transact-sql)
- [FOR JSON (SQL Server)](https://learn.microsoft.com/en-us/sql/relational-databases/json/format-query-results-as-json-with-for-json-sql-server)

---

**[← Previous](./01-ctes-window-functions.md) | [↑ Back to Section](./README.md) | [Next →](./03-regex-fuzzy-matching.md)**
