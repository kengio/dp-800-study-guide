---
title: "JSON Functions — Quick Reference"
type: cheat-sheet
tags:
  - dp-800
  - cheat-sheet
  - json
  - tsql
---

# JSON Functions — Quick Reference

All JSON functions available in Azure SQL Database and SQL Server 2022+, with syntax and examples.

> [!abstract] Quick Reference
>
> - All JSON functions: scalar extraction, construction, OPENJSON parsing, and FOR JSON serialization
> - Lax vs strict mode, JSON indexing strategies, and common JSON manipulation patterns
> - Use when practicing JSON-related questions or building JSON query patterns

---

## JSON Function Summary

> [!info] This table maps every JSON function to its purpose — use it to quickly identify the right function for each scenario.

| Function | Purpose | Returns |
| :--- | :--- | :--- |
| `ISJSON()` | Validate JSON string | 1 or 0 |
| `JSON_VALUE()` | Extract scalar value | NVARCHAR(4000) |
| `JSON_QUERY()` | Extract object or array | NVARCHAR(MAX) |
| `JSON_MODIFY()` | Update value in JSON | NVARCHAR(MAX) |
| `JSON_PATH_EXISTS()` | Check if path exists | 1 or 0 |
| `JSON_OBJECT()` | Build JSON object | NVARCHAR(MAX) |
| `JSON_ARRAY()` | Build JSON array | NVARCHAR(MAX) |
| `JSON_ARRAYAGG()` | Aggregate rows into array | NVARCHAR(MAX) |
| `JSON_OBJECTAGG()` | Aggregate key-value pairs | NVARCHAR(MAX) |
| ==`OPENJSON()`== | Parse JSON to rowset | Table |
| `FOR JSON PATH` | Serialize rows to JSON | NVARCHAR(MAX) |
| `FOR JSON AUTO` | Serialize rows (auto-nesting) | NVARCHAR(MAX) |

---

## Scalar Functions

> [!info] Scalar functions extract, modify, and validate individual values within a JSON document.

### ISJSON

```sql
-- Returns 1 if valid JSON, 0 otherwise
SELECT ISJSON('{"name": "Alice"}');     -- 1
SELECT ISJSON('not json');              -- 0

-- Optional type argument (SQL Server 2022+)
SELECT ISJSON('123', VALUE);            -- 1 (scalar)
SELECT ISJSON('[1,2]', ARRAY);          -- 1
SELECT ISJSON('{"a":1}', OBJECT);       -- 1
SELECT ISJSON('"text"', SCALAR);        -- 1
```

### JSON_VALUE — Extract Scalar

```sql
DECLARE @json NVARCHAR(MAX) = N'{
    "customer": { "id": 42, "name": "Alice" },
    "items": [{"sku": "A1", "qty": 3}]
}';

-- Lax mode (default): returns NULL if path missing
SELECT JSON_VALUE(@json, '$.customer.name');        -- Alice
SELECT JSON_VALUE(@json, '$.customer.phone');       -- NULL

-- Strict mode: raises error if path missing
SELECT JSON_VALUE(@json, 'strict $.customer.phone');
-- Error: Property cannot be found on the specified JSON path.

-- Array element access
SELECT JSON_VALUE(@json, '$.items[0].sku');         -- A1
```

> [!tip] Exam Tip
> `JSON_VALUE` returns NVARCHAR(4000). For larger values or objects/arrays, use `JSON_QUERY`.

### JSON_QUERY — Extract Object or Array

```sql
-- Returns object
SELECT JSON_QUERY(@json, '$.customer');
-- {"id": 42, "name": "Alice"}

-- Returns array
SELECT JSON_QUERY(@json, '$.items');
-- [{"sku": "A1", "qty": 3}]

-- Returns NULL for scalars (not an error in lax mode)
SELECT JSON_QUERY(@json, '$.customer.name');        -- NULL
```

| Scenario | JSON_VALUE | JSON_QUERY |
| :--- | :--- | :--- |
| Scalar (string, number) | ==Returns value== | NULL |
| Object `{}` | NULL | Returns object |
| Array `[]` | NULL | Returns array |

> [!warning] Common Mistake
> Using JSON_VALUE to extract an object or array returns NULL (not an error) in lax mode. Use JSON_QUERY for objects/arrays and JSON_VALUE only for scalars.

### JSON_MODIFY — Update JSON

```sql
DECLARE @doc NVARCHAR(MAX) = N'{"name":"Alice","age":30}';

-- Update existing property
SELECT JSON_MODIFY(@doc, '$.age', 31);
-- {"name":"Alice","age":31}

-- Add new property
SELECT JSON_MODIFY(@doc, '$.email', 'alice@example.com');
-- {"name":"Alice","age":30,"email":"alice@example.com"}

-- Delete property (set to NULL with strict)
SELECT JSON_MODIFY(@doc, '$.age', NULL);
-- {"name":"Alice"}

-- Append to array
DECLARE @arr NVARCHAR(MAX) = N'{"tags":["sql","azure"]}';
SELECT JSON_MODIFY(@arr, 'append $.tags', 'dp800');
-- {"tags":["sql","azure","dp800"]}

-- Insert raw JSON (use JSON_QUERY to avoid double-escaping)
SELECT JSON_MODIFY(@doc, '$.address', JSON_QUERY('{"city":"Seattle"}'));
-- {"name":"Alice","age":30,"address":{"city":"Seattle"}}
```

> [!warning] Common Mistake
> When inserting a JSON object with JSON_MODIFY, wrap the value in JSON_QUERY() to avoid double-escaping. Without JSON_QUERY, the object is treated as a plain string and gets escaped.

### JSON_PATH_EXISTS

```sql
SELECT JSON_PATH_EXISTS(@json, '$.customer.name');   -- 1
SELECT JSON_PATH_EXISTS(@json, '$.customer.phone');  -- 0
```

---

## Construction Functions (SQL Server 2022+ / Azure SQL)

> [!info] Construction functions (SQL Server 2022+) build JSON objects and arrays directly in T-SQL without string concatenation.

### JSON_OBJECT

```sql
-- From literal values
SELECT JSON_OBJECT('name': 'Alice', 'age': 30);
-- {"name":"Alice","age":30}

-- From column values
SELECT JSON_OBJECT('id': CustomerID, 'name': Name) AS CustomerJson
FROM dbo.Customers;

-- Nested objects
SELECT JSON_OBJECT(
    'customer': JSON_OBJECT('id': c.CustomerID, 'name': c.Name),
    'total': SUM(o.TotalAmount)
)
FROM dbo.Customers c
JOIN dbo.Orders o ON c.CustomerID = o.CustomerID
GROUP BY c.CustomerID, c.Name;
```

### JSON_ARRAY

```sql
SELECT JSON_ARRAY(1, 'two', 3, NULL);
-- [1,"two",3]                    -- NULLs omitted by default

SELECT JSON_ARRAY(1, 'two', 3, NULL NULL ON NULL);
-- [1,"two",3,null]               -- NULLs included
```

### JSON_ARRAYAGG / JSON_OBJECTAGG

```sql
-- Aggregate all customer names into a JSON array
SELECT JSON_ARRAYAGG(Name ORDER BY Name)
FROM dbo.Customers;
-- ["Alice","Bob","Carol"]

-- Aggregate into key-value object
SELECT JSON_OBJECTAGG(Name: Email)
FROM dbo.Customers;
-- {"Alice":"alice@example.com","Bob":"bob@example.com"}
```

---

## OPENJSON — Parse JSON to Rows

> [!info] **OPENJSON** shreds JSON into a relational rowset — it is the primary tool for importing and querying JSON data.

### Default Schema (key/value/type)

```sql
DECLARE @json NVARCHAR(MAX) = N'{"name":"Alice","age":30,"active":true}';

SELECT * FROM OPENJSON(@json);
```

| key | value | type |
| :--- | :--- | :--- |
| name | Alice | 1 |
| age | 30 | 2 |
| active | true | 3 |

Type codes: 0=null, 1=string, 2=number, 3=boolean, 4=array, 5=object.

### Explicit Schema (WITH clause)

```sql
DECLARE @data NVARCHAR(MAX) = N'[
    {"id": 1, "name": "Alice", "tags": ["sql","ai"]},
    {"id": 2, "name": "Bob",   "tags": ["azure"]}
]';

SELECT id, name, tags
FROM OPENJSON(@data)
WITH (
    id   INT           '$.id',
    name NVARCHAR(100) '$.name',
    tags NVARCHAR(MAX) '$.tags' AS JSON   -- preserve as JSON
);
```

> [!tip] Exam Tip
> Use `AS JSON` in the WITH clause to preserve nested JSON as a string column. Without it, OPENJSON tries to extract a scalar and returns NULL for objects/arrays.

### Nested OPENJSON with CROSS APPLY

```sql
SELECT o.OrderID, i.ProductName, i.Qty
FROM dbo.Orders o
CROSS APPLY OPENJSON(o.OrderData, '$.items')
WITH (
    ProductName NVARCHAR(100) '$.name',
    Qty         INT           '$.qty'
) i
WHERE o.OrderDate > '2025-01-01';
```

---

## FOR JSON — Serialize to JSON

> [!info] FOR JSON serializes query results into JSON output — PATH gives you full control, AUTO infers nesting from joins.

### FOR JSON PATH

```sql
SELECT CustomerID, Name AS 'info.name', Email AS 'info.email'
FROM dbo.Customers
FOR JSON PATH, ROOT('customers'), INCLUDE_NULL_VALUES;
```

| Clause | Effect |
| :--- | :--- |
| `ROOT('name')` | Wraps result in `{"name": [...]}` |
| `INCLUDE_NULL_VALUES` | Includes `null` for NULL columns |
| `WITHOUT_ARRAY_WRAPPER` | Returns single object, no `[]` |

### FOR JSON AUTO

```sql
SELECT c.CustomerID, c.Name, o.OrderID, o.TotalAmount
FROM dbo.Customers c
JOIN dbo.Orders o ON c.CustomerID = o.CustomerID
FOR JSON AUTO;
-- Auto-nests Orders array inside each Customer
```

---

## Indexing JSON Columns

> [!info] JSON columns cannot be indexed directly — use computed columns with JSON_VALUE to enable index-based lookups.

```sql
-- Computed column + index for fast JSON scalar lookups
ALTER TABLE dbo.Customers
    ADD Email_Computed AS JSON_VALUE(ProfileData, '$.email');

CREATE INDEX IX_Customers_Email
    ON dbo.Customers (Email_Computed);

-- Use in queries — optimizer uses the index
SELECT * FROM dbo.Customers
WHERE JSON_VALUE(ProfileData, '$.email') = 'alice@example.com';
```

---

## Strict vs Lax Mode Summary

> [!info] Mode selection determines whether missing paths return NULL silently or raise an error.

| Behavior | Lax (default) | Strict |
| :--- | :--- | :--- |
| Path not found | ==Returns NULL== | Raises error |
| Type mismatch (e.g., JSON_VALUE on object) | Returns NULL | Raises error |
| Syntax | `$.path` | `strict $.path` |

---

## Common Patterns

> [!info] These patterns combine multiple JSON functions for real-world scenarios commonly tested on the exam.

### Validate before INSERT

```sql
ALTER TABLE dbo.Documents
    ADD CONSTRAINT CK_ValidJson CHECK (ISJSON(Content) = 1);
```

### Update column in-place

```sql
UPDATE dbo.Customers
SET ProfileData = JSON_MODIFY(ProfileData, '$.lastLogin', SYSUTCDATETIME())
WHERE CustomerID = 42;
```

### Shred JSON array into rows for aggregation

```sql
SELECT c.CustomerID,
       COUNT(*) AS TagCount
FROM dbo.Customers c
CROSS APPLY OPENJSON(c.ProfileData, '$.tags') t
GROUP BY c.CustomerID;
```

---

## Gotchas & Traps

- **JSON_VALUE on an object/array path returns NULL** — not an error. If your path points to `{"specs":{"ram":16}}`, `JSON_VALUE(col, '$.specs')` returns NULL. Use `JSON_QUERY` for objects and arrays.
- **Lax mode (default) vs strict mode** — lax returns NULL on path errors; strict throws an error. Prefix path with `strict` to fail fast: `JSON_VALUE(col, 'strict $.name')`.
- **OPENJSON column definition** — without a WITH clause, OPENJSON returns (key, value, type) rows. With a WITH clause, it returns typed columns. The exam tests both forms.
- **FOR JSON PATH vs FOR JSON AUTO** — PATH gives you full control over nesting with dot-notation aliases; AUTO infers structure from table/column names. AUTO can't produce all structures.
- **JSON_MODIFY mutates a copy** — it does NOT update the column in place. You must UPDATE the column: `UPDATE t SET col = JSON_MODIFY(col, '$.path', value)`.
- **ISJSON returns 1/0/NULL** — 1 = valid JSON, 0 = invalid, NULL = input is NULL. Use it in CHECK constraints: `CHECK (ISJSON(col) = 1)`.

---

## Before the Exam, I Can…

- [ ] Explain the difference between JSON_VALUE (scalar), JSON_QUERY (object/array), and OPENJSON (table rows)
- [ ] Write an OPENJSON query both without a WITH clause (key/value/type) and with a WITH clause (typed columns)
- [ ] Explain lax vs strict path mode and when each throws vs returns NULL
- [ ] Write a FOR JSON PATH query with nested objects using dot-notation column aliases
- [ ] Use JSON_MODIFY to update a specific path in a JSON column via UPDATE
- [ ] Explain how to index JSON data using a computed column + regular index

---

**[← Back to Cheat Sheets](./cheat-sheets.md)**
