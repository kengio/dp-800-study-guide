---
title: Constraints and Sequences
type: study-material
tags:
  - dp-800
  - constraints
  - primary-key
  - foreign-key
  - sequences
---

# Constraints and Sequences

## Overview

Constraints enforce data integrity at the database level. SQL Server supports PRIMARY KEY, FOREIGN KEY, UNIQUE, CHECK, and DEFAULT constraints. SEQUENCES provide database-wide, shareable, non-identity number generators.

> [!abstract]
> - Covers PRIMARY KEY, FOREIGN KEY, CHECK, DEFAULT, UNIQUE constraints, and SEQUENCE objects
> - Constraints enforce data integrity at the database level; sequences provide independent number generation
> - Key exam topics: SEQUENCE vs IDENTITY, constraint types and enforcement timing

> [!tip] What the Exam Tests
> - `SEQUENCE` is **independent of any table** — can be shared across tables, cycled, and reset with `ALTER SEQUENCE`
> - `IDENTITY` is **column-bound** — cannot be shared, cannot be reset cleanly without DBCC, increments only upward
> - `CHECK` constraints can reference multiple columns in the same row; `FOREIGN KEY` enforces referential integrity across tables

## Constraint Types

### PRIMARY KEY

```sql
-- Inline (single column)
CREATE TABLE dbo.Customers (
    CustomerId  int NOT NULL IDENTITY(1,1) PRIMARY KEY,
    Name        nvarchar(100) NOT NULL
);

-- Table-level (composite or named)
CREATE TABLE dbo.OrderItems (
    OrderId     int NOT NULL,
    ProductId   int NOT NULL,
    Quantity    int NOT NULL,
    CONSTRAINT PK_OrderItems PRIMARY KEY (OrderId, ProductId)
);
```

- Implicitly creates a unique clustered index (by default)
- Can be made non-clustered: `PRIMARY KEY NONCLUSTERED`
- Only one per table; columns must be NOT NULL

### FOREIGN KEY

```sql
CREATE TABLE dbo.Orders (
    OrderId     int NOT NULL PRIMARY KEY,
    CustomerId  int NOT NULL,
    CONSTRAINT FK_Orders_Customers
        FOREIGN KEY (CustomerId) REFERENCES dbo.Customers (CustomerId)
        ON DELETE NO ACTION
        ON UPDATE CASCADE
);
```

**Referential actions:**

| Action | On DELETE | On UPDATE |
| :--- | :--- | :--- |
| `NO ACTION` (default) | Error if child rows exist | Error if referenced key changes |
| `CASCADE` | Delete child rows | Update child FK values |
| `SET NULL` | Set FK to NULL | Set FK to NULL |
| `SET DEFAULT` | Set FK to column default | Set FK to column default |

### UNIQUE

```sql
-- Unique constraint (allows one NULL)
ALTER TABLE dbo.Customers
ADD CONSTRAINT UQ_Customers_Email UNIQUE (Email);

-- Unique index (equivalent, but more options)
CREATE UNIQUE NONCLUSTERED INDEX UIX_Customers_Email
ON dbo.Customers (Email)
WHERE Email IS NOT NULL;  -- Filtered: exclude NULLs
```

### CHECK

```sql
CREATE TABLE dbo.Products (
    ProductId   int             NOT NULL PRIMARY KEY,
    Price       decimal(10,2)   NOT NULL,
    Quantity    int             NOT NULL,
    Status      varchar(20)     NOT NULL,
    CONSTRAINT CHK_Products_Price    CHECK (Price > 0),
    CONSTRAINT CHK_Products_Quantity CHECK (Quantity >= 0),
    CONSTRAINT CHK_Products_Status   CHECK (Status IN ('active', 'discontinued', 'pending'))
);
```

### DEFAULT

```sql
CREATE TABLE dbo.AuditLog (
    LogId       int             NOT NULL IDENTITY PRIMARY KEY,
    EventType   nvarchar(50)    NOT NULL,
    CreatedAt   datetime2(0)    NOT NULL DEFAULT GETUTCDATE(),
    CreatedBy   nvarchar(128)   NOT NULL DEFAULT SUSER_SNAME(),
    IsProcessed bit             NOT NULL DEFAULT 0
);
```

## Disabling and Enabling Constraints

```sql
-- Disable FK during bulk load
ALTER TABLE dbo.Orders NOCHECK CONSTRAINT FK_Orders_Customers;

-- Re-enable and verify existing data
ALTER TABLE dbo.Orders WITH CHECK CHECK CONSTRAINT FK_Orders_Customers;

-- Disable all constraints on a table
ALTER TABLE dbo.Orders DISABLE TRIGGER ALL;
```

## SEQUENCES

A SEQUENCE is a schema-bound object that generates a sequence of numeric values, independent of any table — useful when the same sequence must be shared across tables.

```sql
-- Create a sequence
CREATE SEQUENCE dbo.OrderNumberSeq
    AS int
    START WITH 10000
    INCREMENT BY 1
    MINVALUE 10000
    MAXVALUE 99999
    CYCLE
    CACHE 50;

-- Use the sequence
INSERT INTO dbo.Orders (OrderId, CustomerId)
VALUES (NEXT VALUE FOR dbo.OrderNumberSeq, 1);

-- Get current value without incrementing
SELECT current_value FROM sys.sequences
WHERE name = 'OrderNumberSeq';

-- Use as default in table
CREATE TABLE dbo.Invoices (
    InvoiceId   int NOT NULL DEFAULT (NEXT VALUE FOR dbo.OrderNumberSeq) PRIMARY KEY,
    Amount      decimal(10,2) NOT NULL
);
```

> [!warning] Common Mistake
> IDENTITY and SEQUENCE both generate sequential numbers, but IDENTITY cannot be shared across tables and is tied to a specific column. If the exam scenario requires a shared counter across multiple tables, the answer is SEQUENCE.

**SEQUENCE vs IDENTITY comparison:**

| Aspect | IDENTITY | SEQUENCE |
| :--- | :--- | :--- |
| Scope | Single table | Schema-wide, multi-table |
| Start/restart | Cannot restart easily | `ALTER SEQUENCE ... RESTART` |
| Caching | No | Yes (`CACHE n`) — faster but gaps on crash |
| Use in SELECT | No | `NEXT VALUE FOR` in any query |
| Transaction rollback | No gap recovery | No gap recovery (same) |

## CHECK Constraint Patterns

CHECK constraints can encode complex business rules beyond simple comparisons. Key patterns include multi-column checks, pattern matching with LIKE, and deferred validation.

- **Multi-column CHECK**: The expression can reference any columns in the same row, enabling cross-column business rules
- **LIKE patterns**: Use `[0-9]`, `[A-Z]`, and `%`/`_` wildcards to validate string formats
- **Deterministic functions only**: Non-deterministic functions (e.g., `GETDATE()`, `RAND()`) are not allowed in CHECK expressions
- **NOT FOR REPLICATION**: Skips the constraint during replication agent operations; constraint still fires for normal user writes
- **WITH NOCHECK**: Adds the constraint without scanning existing rows — useful for large tables but marks the constraint as "not trusted"

```sql
-- Pattern validation
ALTER TABLE Customers ADD CONSTRAINT CK_Phone
    CHECK (Phone LIKE '[0-9][0-9][0-9]-[0-9][0-9][0-9]-[0-9][0-9][0-9][0-9]');

-- Multi-column: end date must be after start date
ALTER TABLE Projects ADD CONSTRAINT CK_ProjectDates
    CHECK (EndDate IS NULL OR EndDate > StartDate);

-- Add without validating existing data
ALTER TABLE Orders WITH NOCHECK ADD CONSTRAINT CK_Positive
    CHECK (TotalAmount > 0);

-- Check if constraint is trusted (validated)
SELECT name, is_not_trusted FROM sys.check_constraints WHERE parent_object_id = OBJECT_ID('Orders');
```

A constraint added with `WITH NOCHECK` sets `is_not_trusted = 1` in `sys.check_constraints`. The query optimizer cannot use an untrusted constraint for plan optimizations. To trust it, run `ALTER TABLE ... WITH CHECK CHECK CONSTRAINT ...`.

## Cascading Referential Actions

ON DELETE and ON UPDATE actions define what happens to child rows when a parent row is deleted or its key is changed.

| Action | Behavior |
| :--- | :--- |
| `NO ACTION` | Raises an error; transaction rolls back if child rows exist |
| `CASCADE` | Automatically deletes or updates matching child rows |
| `SET NULL` | Sets the FK column(s) to NULL (columns must be nullable) |
| `SET DEFAULT` | Sets the FK column(s) to their defined default value |

**Circular reference limitation**: SQL Server does not allow `CASCADE` in a referential cycle. Self-referencing tables or mutual FK cycles must use `NO ACTION` and handle deletes manually (e.g., set ManagerID to NULL before deleting the manager row).

**Multi-level chains**: CASCADE fires recursively. A delete on a grandparent table can cascade through two or more child tables automatically, which can delete more rows than expected.

```sql
-- CASCADE: delete child rows when parent is deleted
ALTER TABLE OrderItems
ADD CONSTRAINT FK_OrderItems_Orders
    FOREIGN KEY (OrderID) REFERENCES Orders(OrderID)
    ON DELETE CASCADE
    ON UPDATE NO ACTION;

-- SET NULL: nullify FK when parent deleted (column must be nullable)
ALTER TABLE Employees
ADD CONSTRAINT FK_Employees_Manager
    FOREIGN KEY (ManagerID) REFERENCES Employees(EmployeeID)
    ON DELETE SET NULL;
```

## Sequence Cycling and Caching

Beyond basic creation, sequences support fine-grained control over cycling behavior and in-memory caching.

- **CYCLE / NO CYCLE**: When the sequence reaches MAXVALUE, `CYCLE` wraps back to MINVALUE; `NO CYCLE` raises an error instead
- **CACHE n**: Pre-allocates `n` values in memory, reducing disk I/O per call; SQL Server writes the "next batch start" to disk, not each individual value
- **NO CACHE**: Every `NEXT VALUE FOR` call writes to disk — no gaps, but higher I/O overhead
- **Gap behavior**: On a server restart, all in-memory cached values are lost. The sequence resumes at the start of the next uncached batch, creating a gap equal to the unused portion of the cache
- **RESTART WITH**: Resets the current position to any valid value; useful for testing or re-seeding

```sql
-- Sequence with cycling and caching
CREATE SEQUENCE dbo.OrderSeq
    AS INT
    START WITH 1
    INCREMENT BY 1
    MINVALUE 1
    MAXVALUE 9999999
    CYCLE
    CACHE 50;

-- Reset sequence
ALTER SEQUENCE dbo.OrderSeq RESTART WITH 1;

-- Peek at next value without incrementing
SELECT current_value FROM sys.sequences WHERE name = 'OrderSeq';

-- Use sequence in default
ALTER TABLE Orders ADD CONSTRAINT DF_OrderID DEFAULT (NEXT VALUE FOR dbo.OrderSeq) FOR OrderID;
```

## UNIQUE Constraints vs UNIQUE Indexes

A UNIQUE constraint and a unique index are nearly identical in SQL Server — the constraint is implemented as a unique non-clustered index behind the scenes.

| Feature | UNIQUE Constraint | Filtered UNIQUE Index |
| :--- | :--- | :--- |
| Allows NULLs | One NULL per column | Multiple NULLs (NULLs excluded from index) |
| Syntax | `ADD CONSTRAINT ... UNIQUE` | `CREATE UNIQUE INDEX ... WHERE col IS NOT NULL` |
| Visible in SSMS | As a constraint | As an index |

- A UNIQUE constraint permits exactly **one NULL** because SQL Server considers a second NULL a duplicate
- A **filtered unique index** with `WHERE col IS NOT NULL` excludes NULLs entirely, allowing multiple NULL values in the column

```sql
-- Filtered unique index: multiple NULLs allowed, non-NULLs must be unique
CREATE UNIQUE NONCLUSTERED INDEX UIX_Employees_NationalID
ON dbo.Employees (NationalID)
WHERE NationalID IS NOT NULL;
```

## Use Cases

- **PRIMARY KEY**: Every table should have one — defines entity identity
- **FOREIGN KEY**: Enforce referential integrity between related tables
- **CHECK**: Enforce domain rules (valid statuses, positive values, date ranges)
- **SEQUENCE**: Invoice numbers, order numbers shared across multiple tables

## Common Issues & Errors

| Error | Cause | Resolution |
| :--- | :--- | :--- |
| FK violation on INSERT | Referenced row doesn't exist | Insert parent row first; or disable FK temporarily |
| Duplicate key on INSERT | UNIQUE or PK violation | Check for existing values; use `MERGE` or upsert |
| CHECK constraint violation | Value fails the condition | Validate at application layer before insert |
| SEQUENCE cache gap | Server restart with CACHE | Use `NO CACHE` for sequential gaps (slower) |
| Cascade cycle error | FK chain creates a cycle | Use `NO ACTION` on one FK; handle deletes in code |
| Untrusted constraint | Added with `WITH NOCHECK` | Re-validate with `WITH CHECK CHECK CONSTRAINT` |

## Best Practices

- Always name constraints explicitly (`CONSTRAINT PK_...`, `CONSTRAINT FK_...`) rather than relying on system-generated names — improves maintainability and scripting
- Prefer `WITH CHECK CHECK CONSTRAINT` when re-enabling disabled constraints to ensure existing data is validated and the constraint is trusted
- Use `WITH NOCHECK` only during large bulk migrations; immediately validate and trust the constraint afterward
- Avoid `CASCADE DELETE` on wide FK chains — explicit deletes in stored procedures are easier to audit and debug
- Use `NO CACHE` sequences only when gaps are truly unacceptable; the performance cost can be significant at high insert rates

## Exam Tips

- `PRIMARY KEY` creates a clustered index by default — can be overridden with `NONCLUSTERED`
- `UNIQUE` allows one NULL value per column; a filtered unique index can exclude NULLs entirely
- `CHECK` constraints added with `WITH NOCHECK` are marked `is_not_trusted = 1` — the optimizer ignores them for plan simplification
- `SEQUENCE` can `CYCLE` (wrap around) and `CACHE` values for performance; cached values are lost on server restart
- `CASCADE` cannot be used in a circular FK reference — SQL Server raises an error at constraint creation time
- `NOT FOR REPLICATION` on CHECK and FK constraints prevents them from firing during replication agent operations

## Key Takeaways

- Constraints enforce data integrity at the database engine level — not just at the application
- FOREIGN KEY referential actions (`CASCADE`, `SET NULL`, `SET DEFAULT`) control child row behavior
- SEQUENCES are more flexible than IDENTITY but require explicit `NEXT VALUE FOR`
- CHECK constraints added without validation (`WITH NOCHECK`) are untrusted and ignored by the optimizer

## Practice Question

**Practice Question**

A sequence with CACHE 50 has a current value of 450. After a SQL Server restart, the next value returned is 501. Why?

A. The sequence CYCLE option reset it to the start
B. The cached values (451-500) were lost when the server restarted
C. The sequence was altered with RESTART WITH 501
D. A concurrent transaction consumed values 451-500

> [!success]- Answer
> **B — The cached values (451-500) were lost when the server restarted**
>
> When a sequence uses CACHE, SQL Server pre-allocates a batch of values in memory. If the server restarts before all cached values are used, those values are lost and the sequence resumes after the last cached batch. This is by design for performance — use NO CACHE if gaps are unacceptable.

## Related Topics

- [01-Tables & Indexes](./01-tables-indexes.md)
- [05-Partitioning](./05-partitioning.md)

## Official Documentation

- [Constraints (SQL Server)](https://learn.microsoft.com/en-us/sql/relational-databases/tables/unique-constraints-and-check-constraints)
- [CREATE SEQUENCE (Transact-SQL)](https://learn.microsoft.com/en-us/sql/t-sql/statements/create-sequence-transact-sql)

---

**[← Previous](./03-json-columns.md) | [↑ Back to Section](./README.md) | [Next →](./05-partitioning.md)**
