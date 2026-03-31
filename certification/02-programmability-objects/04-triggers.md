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

> [!abstract]
> - Covers DML triggers (AFTER, INSTEAD OF), DDL triggers, INSERTED/DELETED virtual tables
> - Triggers fire automatically in response to data or schema changes
> - Key exam topics: AFTER vs INSTEAD OF behavior, INSERTED/DELETED table contents in UPDATE, DDL trigger scope

> [!tip] What the Exam Tests
> - `AFTER` trigger fires **after** the DML statement succeeds; `INSTEAD OF` fires **in place of** the DML (statement does not execute automatically)
> - In an UPDATE trigger: `INSERTED` contains **new** values; `DELETED` contains **old** (pre-update) values — both virtual tables are populated
> - `INSTEAD OF` triggers on views enable updates to non-updatable views (e.g., views joining multiple tables)

---

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
| UPDATE | ==New values== | Old values |

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

> [!warning] Common Mistake
> With an INSTEAD OF trigger, the original DML statement does NOT execute. The trigger is responsible for performing the actual data change if desired. Forgetting to include the INSERT/UPDATE/DELETE inside the trigger body means the change is silently lost.

---

## INSTEAD OF Triggers on Views

Multi-table views and views with aggregates are not directly updatable. INSTEAD OF triggers make these views accept DML by intercepting the statement and routing it manually to the underlying tables.

Key behaviors:

- The trigger fires **instead of** the DML — the original statement never executes
- You must explicitly write the INSERT/UPDATE/DELETE in the trigger body
- Supported: INSTEAD OF INSERT, INSTEAD OF UPDATE, INSTEAD OF DELETE
- Fires **before** constraint checking (unlike AFTER triggers)

```sql
-- View joining two tables (not directly updatable)
CREATE VIEW vw_OrderDetails
AS SELECT o.OrderID, o.TotalAmount, c.Name, c.Email
   FROM Orders o JOIN Customers c ON o.CustomerID = c.CustomerID;

-- INSTEAD OF INSERT on the view
CREATE TRIGGER trg_IOI_OrderDetails
ON vw_OrderDetails
INSTEAD OF INSERT
AS
BEGIN
    SET NOCOUNT ON;
    -- Insert customer first
    INSERT INTO Customers (Name, Email)
    SELECT i.Name, i.Email FROM inserted i
    WHERE NOT EXISTS (SELECT 1 FROM Customers c WHERE c.Email = i.Email);

    -- Then insert order
    INSERT INTO Orders (CustomerID, TotalAmount)
    SELECT c.CustomerID, i.TotalAmount
    FROM inserted i
    JOIN Customers c ON c.Email = i.Email;
END;
```

---

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

### DDL Trigger Details

- **Scope:** database-level (`ON DATABASE`) or server-level (`ON ALL SERVER`)
- **Common events:** `CREATE_TABLE`, `ALTER_TABLE`, `DROP_TABLE`, `CREATE_PROCEDURE`, `ALTER_PROCEDURE`, `DROP_PROCEDURE`
- **`EVENTDATA()`:** returns an XML document containing event type, object name, login name, TSQL text, and more
- **Typical use cases:** audit schema changes, prevent accidental table or database drops in production

```sql
-- Prevent dropping tables in production
CREATE TRIGGER trg_PreventDrop
ON DATABASE
FOR DROP_TABLE
AS
BEGIN
    PRINT 'Table drops are not allowed. Contact DBA team.';
    ROLLBACK;
END;

-- Audit DDL changes to a log table
CREATE TRIGGER trg_AuditDDL
ON DATABASE
FOR CREATE_TABLE, ALTER_TABLE, DROP_TABLE
AS
BEGIN
    INSERT INTO DDLAuditLog (EventType, ObjectName, LoginName, EventTime, EventData)
    SELECT
        EVENTDATA().value('(/EVENT_INSTANCE/EventType)[1]', 'NVARCHAR(100)'),
        EVENTDATA().value('(/EVENT_INSTANCE/ObjectName)[1]', 'NVARCHAR(200)'),
        EVENTDATA().value('(/EVENT_INSTANCE/LoginName)[1]', 'NVARCHAR(200)'),
        GETUTCDATE(),
        EVENTDATA();
END;
```

---

## Trigger Execution Order

When multiple triggers exist for the same event on the same table, use `sp_settriggerorder` to designate which fires FIRST or LAST. Intermediate triggers fire in an undefined order.

- **Nested triggers:** a trigger that performs DML on another table can fire that table's trigger (up to 32 levels deep)
- **Recursive triggers:** an UPDATE inside a trigger on table T fires T's own trigger again — disabled by default (`RECURSIVE_TRIGGERS OFF`)
- **Maximum nesting level:** 32; exceeding it raises an error and rolls back the transaction

```sql
-- Set trigger execution order
EXEC sp_settriggerorder
    @triggername = 'trg_AuditUpdate',
    @order = 'First',
    @stmttype = 'UPDATE';

-- Check if recursive triggers are enabled
SELECT name, is_recursive_triggers_on
FROM sys.databases WHERE name = DB_NAME();
```

---

## Logon Triggers

Logon triggers are server-scoped triggers that fire when a SQL Server login session is established (after authentication but before the session is fully open).

- **Scope:** server-level — defined with `ON ALL SERVER`
- **Use cases:** restrict logins to business hours, enforce IP-based access control, log all connection attempts
- **ROLLBACK** inside a logon trigger terminates the connection before it fully opens
- Logon triggers do **not** have access to `inserted`/`deleted` tables; use `EVENTDATA()` or `ORIGINAL_LOGIN()` instead

```sql
-- Restrict logins to business hours (Mon-Fri, 08:00-18:00)
CREATE TRIGGER trg_RestrictLoginHours
ON ALL SERVER
FOR LOGON
AS
BEGIN
    DECLARE @Hour int = DATEPART(HOUR, GETDATE());
    DECLARE @Weekday int = DATEPART(WEEKDAY, GETDATE());

    -- Weekday: 1=Sun, 7=Sat; block weekends and outside 08-18
    IF @Weekday IN (1, 7) OR @Hour < 8 OR @Hour >= 18
    BEGIN
        IF ORIGINAL_LOGIN() <> 'sa'  -- allow emergency SA access
        BEGIN
            PRINT 'Logins are only allowed Mon-Fri 08:00-18:00.';
            ROLLBACK;
        END;
    END;
END;
```

---

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

---

## Use Cases

- **Auditing**: Track who changed what and when without modifying application code
- **Enforcing complex rules**: Business logic that can't be expressed as CHECK constraints
- **Synchronizing derived data**: Maintain denormalized columns or summary tables
- **View DML**: Enable INSERT/UPDATE/DELETE on views with complex logic
- **Schema governance**: DDL triggers prevent unauthorized drops or changes in production

---

## Common Issues & Errors

| Issue | Cause | Resolution |
| :--- | :--- | :--- |
| Trigger fires once for multi-row DML | `inserted`/`deleted` tables have multiple rows | ==Write set-based logic, not `SELECT TOP 1` or scalar variables== |
| Recursive trigger loop | Trigger updates a table that triggers itself | Check `sys.triggers.is_recursive` or disable recursive triggers |
| Performance degradation | Trigger runs synchronously on every DML | Move heavy work to async process (Service Broker, queue) |
| Logon trigger locks everyone out | Faulty ROLLBACK logic in logon trigger | Connect via DAC (`admin:`) to disable or drop the trigger |

---

## Best Practices

- **Write set-based logic**: `inserted` and `deleted` can contain multiple rows — never assume single-row triggers
- **Keep triggers short**: Heavy logic in triggers causes blocking; use async approaches (Service Broker) for long operations
- **Use `SET NOCOUNT ON`**: Prevents extra result sets from being sent to the client and avoids unexpected row-count side effects
- **Avoid recursive triggers**: Can cause infinite loops; disable with `ALTER DATABASE SET RECURSIVE_TRIGGERS OFF`
- **Test logon triggers carefully**: A broken logon trigger can lock all users out; always preserve a DAC or `sa` bypass path

---

## Exam Tips

> [!tip] Exam Tips
> - AFTER triggers fire **after constraints** — if a constraint fails, the trigger doesn't run
> - INSTEAD OF triggers fire **before constraints** — and replace the DML
> - `EVENTDATA()` returns an XML document with details about DDL events
> - Triggers that use `ROLLBACK` inside a TRY/CATCH require careful transaction management
> - A view joining multiple tables requires an **INSTEAD OF** trigger — AFTER triggers cannot make a non-updatable view accept DML
> - Logon triggers use `ON ALL SERVER` and can disconnect users by calling `ROLLBACK`
> - `sp_settriggerorder` controls which trigger fires FIRST or LAST when multiple triggers exist on the same event

---

## Key Takeaways

- `inserted` = new rows; `deleted` = old rows; both populated for UPDATE
- INSTEAD OF triggers on views enable DML on non-updatable views by replacing the statement entirely
- DDL triggers audit or prevent schema changes using `EVENTDATA()`
- Logon triggers enforce connection-level policies at the server scope
- Trigger nesting depth is capped at 32; recursive triggers are off by default

---

## Practice Question

A view joins the Orders and Customers tables. A user tries to INSERT into the view and gets an error. Which trigger type resolves this?

A. AFTER INSERT trigger on the Orders table
B. INSTEAD OF INSERT trigger on the view
C. DDL trigger for CREATE event on the view
D. AFTER INSERT trigger on the view

> [!success]- Answer
> **B — INSTEAD OF INSERT trigger on the view**
>
> INSTEAD OF triggers intercept DML on views and allow you to manually route inserts to the underlying tables. AFTER triggers fire after the DML completes — they cannot make a non-updatable view accept inserts. DDL triggers (C) respond to schema events like CREATE TABLE, not DML. AFTER triggers on views (D) can exist but don't solve the multi-table insert problem.

---

## Related Topics

- [03-Stored Procedures](./03-stored-procedures.md)
- [04-Auditing](../05-data-security-compliance/04-auditing.md)
- [02-Specialized Tables — Ledger](../01-database-objects/02-specialized-tables.md)

---

## Official Documentation

- [DML Triggers (SQL Server)](https://learn.microsoft.com/en-us/sql/relational-databases/triggers/dml-triggers)
- [DDL Triggers (SQL Server)](https://learn.microsoft.com/en-us/sql/relational-databases/triggers/ddl-triggers)
- [Logon Triggers (SQL Server)](https://learn.microsoft.com/en-us/sql/relational-databases/triggers/logon-triggers)

---

**[← Previous](./03-stored-procedures.md) | [↑ Back to Section](./README.md)**
