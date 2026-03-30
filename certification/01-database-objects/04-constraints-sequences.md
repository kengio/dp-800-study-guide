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

**SEQUENCE vs IDENTITY comparison:**

| Aspect | IDENTITY | SEQUENCE |
| :--- | :--- | :--- |
| Scope | Single table | Schema-wide, multi-table |
| Start/restart | Cannot restart easily | `ALTER SEQUENCE ... RESTART` |
| Caching | No | Yes (`CACHE n`) — faster but gaps on crash |
| Use in SELECT | No | `NEXT VALUE FOR` in any query |
| Transaction rollback | No gap recovery | No gap recovery (same) |

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

## Exam Tips

- `PRIMARY KEY` creates a clustered index by default — can be overridden with `NONCLUSTERED`
- `UNIQUE` allows one NULL value per column; a filtered unique index can exclude NULLs entirely
- `CHECK` constraints are disabled by default when using `NOCHECK` — re-enable with `WITH CHECK CHECK`
- `SEQUENCE` can `CYCLE` (wrap around) and `CACHE` values for performance

## Key Takeaways

- Constraints enforce data integrity at the database engine level — not just at the application
- FOREIGN KEY referential actions (`CASCADE`, `SET NULL`, `SET DEFAULT`) control child row behavior
- SEQUENCES are more flexible than IDENTITY but require explicit `NEXT VALUE FOR`

## Related Topics

- [01-Tables & Indexes](./01-tables-indexes.md)
- [05-Partitioning](./05-partitioning.md)

## Official Documentation

- [Constraints (SQL Server)](https://learn.microsoft.com/en-us/sql/relational-databases/tables/unique-constraints-and-check-constraints)
- [CREATE SEQUENCE (Transact-SQL)](https://learn.microsoft.com/en-us/sql/t-sql/statements/create-sequence-transact-sql)

---

**[← Previous](./03-json-columns.md) | [↑ Back to Section](./README.md) | [Next →](./05-partitioning.md)**
