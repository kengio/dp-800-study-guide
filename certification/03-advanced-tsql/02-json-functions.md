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
| 2 | number |
| 3 | true/false |
| 4 | array |
| 5 | object |

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
-- Aggregate rows into a JSON array
SELECT
    CategoryId,
    JSON_ARRAYAGG(Name ORDER BY Name) AS ProductNames
FROM dbo.Products
GROUP BY CategoryId;
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

## Use Cases

- **Storing flexible attributes**: Product metadata, event payloads, configuration
- **API response storage**: Cache raw API responses and query them with JSON functions
- **RAG pipelines**: Convert query results to JSON for LLM prompts using `FOR JSON`
- **Data exchange**: Import/export data in JSON format for microservices

## Common Issues & Errors

| Issue | Cause | Resolution |
| :--- | :--- | :--- |
| `JSON_VALUE` returns NULL | Path not found (lax mode) | Verify path; use `strict` to get an error instead |
| `JSON_QUERY` returns NULL on scalar | Scalar values need `JSON_VALUE` | Use `JSON_VALUE` for strings/numbers, `JSON_QUERY` for objects/arrays |
| `FOR JSON` produces unexpected nesting | Column naming causes auto-nesting | Use explicit aliases or `FOR JSON PATH` with dot notation |

## Exam Tips

- `JSON_VALUE` = scalar → string; `JSON_QUERY` = objects/arrays → JSON fragment
- `OPENJSON` with `WITH` clause provides strongly-typed output — preferred for structured parsing
- `FOR JSON PATH` gives explicit control; `FOR JSON AUTO` infers nesting from aliases
- `JSON_ARRAYAGG` is SQL Server 2022+ — know it for newer platform questions

## Key Takeaways

- Two read functions: `JSON_VALUE` (scalar) and `JSON_QUERY` (object/array)
- `OPENJSON` is the most versatile — converts JSON to relational rows
- `FOR JSON` converts relational results to JSON — essential for RAG prompt building

## Related Topics

- [03-JSON Columns](../01-database-objects/03-json-columns.md)
- [02-RAG Prompts and Responses](../11-rag/02-prompts-and-responses.md)

## Official Documentation

- [JSON Functions (Transact-SQL)](https://learn.microsoft.com/en-us/sql/t-sql/functions/json-functions-transact-sql)
- [OPENJSON (Transact-SQL)](https://learn.microsoft.com/en-us/sql/t-sql/functions/openjson-transact-sql)
- [FOR JSON (SQL Server)](https://learn.microsoft.com/en-us/sql/relational-databases/json/format-query-results-as-json-with-for-json-sql-server)

---

**[← Previous](./01-ctes-window-functions.md) | [↑ Back to Section](./README.md) | [Next →](./03-regex-fuzzy-matching.md)**
