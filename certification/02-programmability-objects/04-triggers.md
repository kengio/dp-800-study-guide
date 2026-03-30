---
title: Triggers
type: study-material
tags:
  - dp-800
  - triggers
  - dml-triggers
  - ddl-triggers
  - instead-of
---

# Triggers

## Overview

Triggers are stored procedures that execute automatically in response to DML (INSERT, UPDATE, DELETE) or DDL (CREATE, ALTER, DROP) events. They are used for auditing, enforcing complex business rules, and maintaining derived data.

## DML Triggers

### AFTER Triggers

AFTER triggers fire after the DML operation and after constraint checking. They have access to `inserted` and `deleted` virtual tables.

```sql
CREATE TRIGGER trg_Orders_Audit
ON dbo.Orders
AFTER INSERT, UPDATE, DELETE
AS
BEGIN
    SET NOCOUNT ON;

    -- Log inserts
    INSERT INTO dbo.OrderAudit (OrderId, Action, ChangedAt, ChangedBy)
    SELECT i.OrderId, 'INSERT', GETUTCDATE(), SUSER_SNAME()
    FROM inserted i
    WHERE NOT EXISTS (SELECT 1 FROM deleted d WHERE d.OrderId = i.OrderId);

    -- Log updates
    INSERT INTO dbo.OrderAudit (OrderId, Action, ChangedAt, ChangedBy)
    SELECT i.OrderId, 'UPDATE', GETUTCDATE(), SUSER_SNAME()
    FROM inserted i
    WHERE EXISTS (SELECT 1 FROM deleted d WHERE d.OrderId = i.OrderId);

    -- Log deletes
    INSERT INTO dbo.OrderAudit (OrderId, Action, ChangedAt, ChangedBy)
    SELECT d.OrderId, 'DELETE', GETUTCDATE(), SUSER_SNAME()
    FROM deleted d
    WHERE NOT EXISTS (SELECT 1 FROM inserted i WHERE i.OrderId = d.OrderId);
END;
```

**`inserted` and `deleted` tables:**
| Operation | `inserted` | `deleted` |
| :--- | :--- | :--- |
| INSERT | New rows | Empty |
| DELETE | Empty | Old rows |
| UPDATE | New values | Old values |

### INSTEAD OF Triggers

INSTEAD OF triggers replace the DML operation entirely — used on views or to intercept inserts with custom logic.

```sql
-- INSTEAD OF INSERT on a view that spans two tables
CREATE TRIGGER trg_vw_CustomerOrders_Insert
ON dbo.vw_CustomerOrders
INSTEAD OF INSERT
AS
BEGIN
    SET NOCOUNT ON;

    -- Insert into Customers if new
    INSERT INTO dbo.Customers (Name)
    SELECT DISTINCT CustomerName FROM inserted
    WHERE CustomerName NOT IN (SELECT Name FROM dbo.Customers);

    -- Insert into Orders
    INSERT INTO dbo.Orders (CustomerId, OrderDate, TotalAmount)
    SELECT c.CustomerId, i.OrderDate, i.TotalAmount
    FROM inserted i
    JOIN dbo.Customers c ON c.Name = i.CustomerName;
END;
```

## DDL Triggers

DDL triggers fire on schema changes — useful for preventing unauthorized schema modifications or auditing.

```sql
-- Server-level: prevent database drops
CREATE TRIGGER trg_PreventDatabaseDrop
ON ALL SERVER
FOR DROP_DATABASE
AS
BEGIN
    PRINT 'Database drops are not allowed.';
    ROLLBACK;
END;

-- Database-level: audit table creations
CREATE TRIGGER trg_AuditTableCreate
ON DATABASE
FOR CREATE_TABLE, ALTER_TABLE, DROP_TABLE
AS
BEGIN
    DECLARE @EventData xml = EVENTDATA();

    INSERT INTO dbo.SchemaChangeLog (EventType, ObjectName, ChangedAt, ChangedBy)
    VALUES (
        @EventData.value('(/EVENT_INSTANCE/EventType)[1]', 'nvarchar(100)'),
        @EventData.value('(/EVENT_INSTANCE/ObjectName)[1]', 'nvarchar(200)'),
        GETUTCDATE(),
        SUSER_SNAME()
    );
END;
```

## Managing Triggers

```sql
-- Disable a trigger
DISABLE TRIGGER trg_Orders_Audit ON dbo.Orders;

-- Enable a trigger
ENABLE TRIGGER trg_Orders_Audit ON dbo.Orders;

-- Disable all triggers on a table
DISABLE TRIGGER ALL ON dbo.Orders;

-- View trigger definition
SELECT definition FROM sys.sql_modules
WHERE object_id = OBJECT_ID('trg_Orders_Audit');
```

## Trigger Best Practices

- **Write set-based logic**: `inserted` and `deleted` can contain multiple rows — never assume single-row triggers
- **Keep triggers short**: Heavy logic in triggers causes blocking; use async approaches for long operations
- **Avoid recursive triggers**: Can cause infinite loops; disable with `ALTER DATABASE SET RECURSIVE_TRIGGERS OFF`
- **Use `SET NOCOUNT ON`**: Prevents extra result sets from being sent to the client

## Use Cases

- **Auditing**: Track who changed what and when without modifying application code
- **Enforcing complex rules**: Business logic that can't be expressed as CHECK constraints
- **Synchronizing derived data**: Maintain denormalized columns or summary tables
- **View DML**: Enable INSERT/UPDATE/DELETE on views with complex logic

## Common Issues & Errors

| Issue | Cause | Resolution |
| :--- | :--- | :--- |
| Trigger fires once for multi-row DML | `inserted`/`deleted` tables have multiple rows | Write set-based logic, not `SELECT TOP 1` or scalar variables |
| Recursive trigger loop | Trigger updates a table that triggers itself | Check `sys.triggers.is_recursive` or disable recursive triggers |
| Performance degradation | Trigger runs synchronously on every DML | Move heavy work to async process (Service Broker, queue) |

## Exam Tips

- AFTER triggers fire **after constraints** — if a constraint fails, the trigger doesn't run
- INSTEAD OF triggers fire **before constraints** — and replace the DML
- `EVENTDATA()` returns an XML document with details about DDL events
- Triggers that use `ROLLBACK` inside a TRY/CATCH require careful transaction management

## Key Takeaways

- `inserted` = new rows; `deleted` = old rows; both populated for UPDATE
- INSTEAD OF triggers on views enable DML on non-updatable views
- DDL triggers audit or prevent schema changes using `EVENTDATA()`

## Related Topics

- [03-Stored Procedures](./03-stored-procedures.md)
- [04-Auditing](../05-data-security-compliance/04-auditing.md)
- [02-Specialized Tables — Ledger](../01-database-objects/02-specialized-tables.md)

## Official Documentation

- [DML Triggers (SQL Server)](https://learn.microsoft.com/en-us/sql/relational-databases/triggers/dml-triggers)
- [DDL Triggers (SQL Server)](https://learn.microsoft.com/en-us/sql/relational-databases/triggers/ddl-triggers)

---

**[← Previous](./03-stored-procedures.md) | [↑ Back to Section](./README.md)**
