---
title: JSON Patterns in T-SQL
type: code-examples
tags:
  - dp-800
  - tsql
  - code-examples
  - json
---

# JSON Patterns in T-SQL

Common JSON patterns for Azure SQL and Fabric SQL — covering construction, parsing, scalar functions, indexing, and SQL Server 2022+ construction functions.

---

## FOR JSON — Constructing JSON Output

Use `FOR JSON` to serialize query results as JSON. Two modes: `PATH` (explicit) and `AUTO` (inferred from table aliases).

```sql
-- FOR JSON PATH: dot notation in aliases creates nested objects
SELECT
    c.CustomerID,
    c.Name        AS 'customer.name',
    c.Email       AS 'customer.email',
    o.OrderID     AS 'orders.id',
    o.TotalAmount AS 'orders.total'
FROM Customers c
JOIN Orders o ON c.CustomerID = o.CustomerID
FOR JSON PATH, ROOT('data');
```

```json
{
  "data": [
    {
      "CustomerID": 1,
      "customer": { "name": "Alice", "email": "alice@example.com" },
      "orders":   { "id": 101, "total": 250.00 }
    }
  ]
}
```

```sql
-- FOR JSON AUTO: nesting is inferred from the JOIN structure and table aliases
-- Each table maps to a nested object automatically
SELECT
    c.CustomerID,
    c.Name,
    o.OrderID,
    o.TotalAmount
FROM Customers c
JOIN Orders o ON c.CustomerID = o.CustomerID
FOR JSON AUTO;
-- Produces: [{"CustomerID":1,"Name":"Alice","o":[{"OrderID":101,"TotalAmount":250.00}]}]
-- Note: AUTO is convenient but gives less control over property names
```

```sql
-- ROOT: wraps the array in a named top-level property
SELECT CustomerID, Name
FROM Customers
FOR JSON PATH, ROOT('customers');

-- WITHOUT_ARRAY_WRAPPER: returns a single object instead of a one-element array
-- Use when the result is guaranteed to be one row (e.g., TOP 1 or singleton query)
SELECT TOP 1 CustomerID, Name
FROM Customers
WHERE CustomerID = 1
FOR JSON PATH, WITHOUT_ARRAY_WRAPPER;

-- INCLUDE_NULL_VALUES: by default NULL columns are omitted from output
-- Add this option to emit explicit null properties
SELECT CustomerID, Name, MiddleName  -- MiddleName may be NULL
FROM Customers
FOR JSON PATH, INCLUDE_NULL_VALUES;
-- Without option: {"CustomerID":1,"Name":"Alice"}
-- With option:    {"CustomerID":1,"Name":"Alice","MiddleName":null}
```

---

## OPENJSON — Parsing JSON Input

`OPENJSON` is a table-valued function that shreds a JSON string into rows. It supports a default schema (three generic columns) or an explicit `WITH` clause for typed output.

```sql
-- Default schema: returns key, value, type columns
-- type values: 0=null, 1=string, 2=number, 3=true/false, 4=array, 5=object
DECLARE @json NVARCHAR(MAX) = '[{"id":1,"amount":100.50},{"id":2,"amount":200.00}]';

SELECT * FROM OPENJSON(@json);
-- key | value                      | type
-- 0   | {"id":1,"amount":100.50}   | 5
-- 1   | {"id":2,"amount":200.00}   | 5
```

```sql
-- WITH clause: typed columns mapped via JSON path expressions
DECLARE @json NVARCHAR(MAX) = '[{"id":1,"amount":100.50},{"id":2,"amount":200.00}]';

SELECT id, amount
FROM OPENJSON(@json)
WITH (
    id     INT            '$.id',
    amount DECIMAL(18, 2) '$.amount'
);
-- id | amount
-- 1  | 100.50
-- 2  | 200.00
```

```sql
-- Parsing nested arrays stored in a column using CROSS APPLY
-- Each Orders row has a LineItemsJSON column like:
-- [{"productId":5,"qty":2},{"productId":9,"qty":1}]
SELECT
    o.OrderID,
    li.ProductID,
    li.Quantity
FROM Orders o
CROSS APPLY OPENJSON(o.LineItemsJSON)
WITH (
    ProductID INT '$.productId',
    Quantity  INT '$.qty'
) AS li;
-- CROSS APPLY: rows with NULL or empty JSON are excluded (use OUTER APPLY to keep them)
```

```sql
-- Extracting a sub-object path: parse only part of the document
DECLARE @order NVARCHAR(MAX) = '{"id":1,"shipping":{"city":"Seattle","zip":"98101"}}';

SELECT city, zip
FROM OPENJSON(@order, '$.shipping')     -- second arg = root path into the document
WITH (
    city NVARCHAR(100) '$.city',
    zip  NVARCHAR(10)  '$.zip'
);
```

---

## JSON Scalar Functions

Four core functions for reading and modifying JSON values inline.

```sql
DECLARE @order NVARCHAR(MAX) =
    '{"id":1,"customer":{"name":"Alice"},"items":[{"sku":"A1","qty":2}]}';

-- JSON_VALUE: extracts a scalar (primitive) value; returns NVARCHAR(4000)
-- Use for strings, numbers, booleans — NOT objects or arrays
SELECT JSON_VALUE(@order, '$.customer.name');    -- 'Alice'
SELECT JSON_VALUE(@order, '$.items[0].sku');     -- 'A1'
SELECT JSON_VALUE(@order, '$.id');               -- '1' (always a string)

-- JSON_VALUE returns NULL (lax mode) if the path points to an object or array
SELECT JSON_VALUE(@order, '$.items');            -- NULL — use JSON_QUERY instead
```

```sql
DECLARE @order NVARCHAR(MAX) =
    '{"id":1,"customer":{"name":"Alice"},"items":[{"sku":"A1","qty":2}]}';

-- JSON_QUERY: extracts an object or array; returns NVARCHAR(MAX)
-- Returns NULL for scalar values — complementary to JSON_VALUE
SELECT JSON_QUERY(@order, '$.customer');         -- {"name":"Alice"}
SELECT JSON_QUERY(@order, '$.items');            -- [{"sku":"A1","qty":2}]
SELECT JSON_QUERY(@order, '$.items[0]');         -- {"sku":"A1","qty":2}
```

```sql
DECLARE @order NVARCHAR(MAX) =
    '{"id":1,"customer":{"name":"Alice"},"items":[{"sku":"A1","qty":2}]}';

-- JSON_MODIFY: returns a *new* JSON string with the modification applied
-- The original variable is NOT changed — JSON is immutable in T-SQL
SELECT JSON_MODIFY(@order, '$.customer.name', 'Bob');
-- {"id":1,"customer":{"name":"Bob"},"items":[{"sku":"A1","qty":2}]}

-- append keyword adds an element to an array
SELECT JSON_MODIFY(
    @order,
    'append $.items',
    JSON_QUERY('{"sku":"B2","qty":1}')  -- JSON_QUERY wraps it as an object, not a string
);
-- items becomes: [{"sku":"A1","qty":2},{"sku":"B2","qty":1}]

-- Setting a path to NULL removes the property (lax mode)
SELECT JSON_MODIFY(@order, '$.customer.name', NULL);  -- removes "name" key

-- Chain multiple JSON_MODIFY calls for multiple updates
SELECT JSON_MODIFY(
    JSON_MODIFY(@order, '$.customer.name', 'Bob'),
    '$.id',
    99
);
```

```sql
-- IS_JSON: validates that a string is well-formed JSON; returns 1, 0, or NULL
-- Use in CHECK constraints and WHERE filters
SELECT IS_JSON('{"valid":true}');                -- 1
SELECT IS_JSON('{bad json}');                    -- 0
SELECT IS_JSON(NULL);                            -- NULL

-- Validate before parsing (avoids runtime errors in OPENJSON)
SELECT OrderID, LineItemsJSON
FROM Orders
WHERE IS_JSON(LineItemsJSON) = 1;

-- Enforce valid JSON in a column via CHECK constraint
ALTER TABLE Orders
ADD CONSTRAINT CK_Orders_LineItemsJSON
    CHECK (LineItemsJSON IS NULL OR IS_JSON(LineItemsJSON) = 1);
```

---

## JSON Construction Functions (SQL Server 2022 / Azure SQL)

SQL Server 2022 and Azure SQL Database added `JSON_OBJECT`, `JSON_ARRAY`, `JSON_ARRAYAGG`, and `JSON_OBJECTAGG` for inline JSON construction without `FOR JSON`.

```sql
-- JSON_OBJECT: build a JSON object inline from key:value pairs
SELECT JSON_OBJECT(
    'name'  : Name,
    'email' : Email,
    'active': IsActive
) AS CustomerJSON
FROM Customers;
-- {"name":"Alice","email":"alice@example.com","active":true}

-- NULL_ON_NULL (default) vs ABSENT_ON_NULL: control null handling
SELECT JSON_OBJECT('name': Name, 'middle': MiddleName ABSENT ON NULL) AS j
FROM Customers;
-- middle property is omitted when MiddleName IS NULL
```

```sql
-- JSON_ARRAY: build a JSON array inline from a list of expressions
SELECT JSON_ARRAY(1, 'text', NULL, GETDATE()) AS MyArray;
-- [1,"text",null,"2026-03-30T00:00:00"]

-- Combine JSON_OBJECT and JSON_ARRAY for structured inline construction
SELECT JSON_ARRAY(
    JSON_OBJECT('id': 1, 'label': 'First'),
    JSON_OBJECT('id': 2, 'label': 'Second')
) AS Steps;
```

```sql
-- JSON_ARRAYAGG: aggregate rows into a JSON array (like STRING_AGG but JSON-aware)
-- Requires SQL Server 2022+ or Azure SQL
SELECT
    CategoryID,
    JSON_ARRAYAGG(
        JSON_OBJECT('name': ProductName, 'price': Price)
    ) AS Products
FROM Products
GROUP BY CategoryID;
-- CategoryID | Products
-- 1          | [{"name":"Widget","price":9.99},{"name":"Gadget","price":19.99}]
```

```sql
-- JSON_OBJECTAGG: aggregate key-value pairs into a single JSON object
-- Each row contributes one property to the result object
SELECT JSON_OBJECTAGG(SettingKey: SettingValue) AS Config
FROM AppSettings
WHERE AppID = 42;
-- {"theme":"dark","pageSize":"25","language":"en-US"}
```

---

## Strict vs Lax Mode

JSON path expressions support two modes. Lax is the default; strict raises an error for missing paths or type mismatches.

```sql
DECLARE @json NVARCHAR(MAX) = '{"name":"Alice"}';

-- Lax (default): missing path returns NULL, no error raised
SELECT JSON_VALUE(@json, 'lax $.age');       -- NULL
SELECT JSON_VALUE(@json, '$.age');            -- NULL (lax is implicit)

-- Strict: missing path raises error 13608 "Property cannot be found"
SELECT JSON_VALUE(@json, 'strict $.age');     -- Error

-- Strict is useful when you want to guarantee the path exists
-- and surface data quality issues early
```

```sql
DECLARE @data NVARCHAR(MAX) = '{"items":[1,2,3]}';

-- Lax with array index out of bounds: returns NULL
SELECT JSON_VALUE(@data, 'lax $.items[9]');   -- NULL

-- Strict with array index out of bounds: raises error
SELECT JSON_VALUE(@data, 'strict $.items[9]'); -- Error

-- Practical pattern: use lax in application queries, strict in ETL/validation
-- to catch unexpected schema changes at load time
SELECT
    JSON_VALUE(Payload, 'strict $.orderId')   AS OrderID,
    JSON_VALUE(Payload, 'strict $.customerId') AS CustomerID
FROM StagingEvents
WHERE EventType = 'OrderCreated';
```

---

## Indexing JSON Columns

JSON columns are stored as `NVARCHAR(MAX)` and are not natively indexable. Use persisted computed columns to expose individual JSON properties for indexing.

```sql
-- Step 1: add a persisted computed column that extracts a JSON property
ALTER TABLE Orders
ADD CustomerCountry AS JSON_VALUE(ShippingJSON, '$.country') PERSISTED;
-- PERSISTED: value is stored on disk and kept in sync automatically
-- Non-persisted computed columns cannot be indexed

-- Step 2: create an index on the computed column
CREATE INDEX IX_Orders_Country ON Orders (CustomerCountry);

-- Step 3: queries filtering on that JSON path now use the index
-- The optimizer recognizes JSON_VALUE(ShippingJSON, '$.country') = computed column
SELECT OrderID, TotalAmount
FROM Orders
WHERE JSON_VALUE(ShippingJSON, '$.country') = 'US';
-- Execution plan: Index Seek on IX_Orders_Country

-- Step 4: covering index — include payload columns to avoid key lookups
CREATE INDEX IX_Orders_Country_Cover
    ON Orders (CustomerCountry)
    INCLUDE (OrderID, TotalAmount, OrderDate);
```

```sql
-- Filtered index: index only the rows that match a condition
-- Useful when most rows have NULL or a default value
CREATE INDEX IX_Orders_PriorityUS
    ON Orders (CustomerCountry, OrderDate)
    WHERE CustomerCountry = 'US';

-- Composite example: index on city + country for multi-column JSON predicates
ALTER TABLE Orders
ADD ShippingCity    AS JSON_VALUE(ShippingJSON, '$.city')    PERSISTED,
    ShippingCountry AS JSON_VALUE(ShippingJSON, '$.country') PERSISTED;

CREATE INDEX IX_Orders_Shipping ON Orders (ShippingCountry, ShippingCity);
```

---

**[← Back to Code Examples](./README.md) | [↑ Back to Certification](../../../README.md)**
