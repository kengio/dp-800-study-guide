---
title: Testing Strategy for SQL Database Projects
type: study-material
tags:
  - dp-800
  - testing
  - unit-tests
  - integration-tests
---

# Testing Strategy for SQL Database Projects

## Overview

A robust testing strategy for database projects combines unit tests (isolated, fast, using mock data) with integration tests (end-to-end, using real data flows). The tSQLt framework is the standard unit testing framework for T-SQL, while reference/static data should be version-controlled alongside schema objects.

> [!abstract]
> - Covers testing approaches for database code: unit tests (tSQLt), integration tests, and end-to-end tests
> - tSQLt is the standard T-SQL unit testing framework — tests run inside transactions that are rolled back
> - Key exam topics: tSQLt test isolation mechanism, test doubles (fakes/mocks), assertion functions

> [!tip] What the Exam Tests
> - tSQLt tests run **inside transactions that are always rolled back** — no permanent data changes from test runs
> - `tSQLt.FakeTable` replaces a real table with an empty copy for test isolation
> - `tSQLt.AssertEquals`, `tSQLt.AssertEqualsTable`, `tSQLt.ExpectException` are the core assertion functions

---

## tSQLt Unit Testing Framework

**tSQLt** is a T-SQL unit testing framework that runs entirely inside SQL Server. Tests are organized into schemas (test classes), and each test is a stored procedure beginning with the word "test".

### Installing tSQLt

```sql
-- Download tSQLt.class.sql from tsqlt.org and run it
-- Then enable CLR and TRUSTWORTHY (required by tSQLt)
EXEC sp_configure 'clr enabled', 1;
RECONFIGURE;

ALTER DATABASE MyDB SET TRUSTWORTHY ON;

-- Verify installation
EXEC tSQLt.Info;
```

### Creating a Test Class

```sql
-- A test class is just a schema with the tSQLt.TestClass extended property
EXEC tSQLt.NewTestClass 'OrderTests';
-- Equivalent to:
CREATE SCHEMA [OrderTests];
EXEC sp_addextendedproperty
    @name = N'tSQLt.TestClass',
    @value = 1,
    @level0type = N'SCHEMA',
    @level0name = N'OrderTests';
```

### Writing a Basic Unit Test

```sql
-- Test that CalculateOrderTotal returns correct value
CREATE OR ALTER PROCEDURE [OrderTests].[test CalculateOrderTotal returns correct sum]
AS
BEGIN
    -- Arrange: create a fake Orders table with controlled data
    EXEC tSQLt.FakeTable 'dbo.Orders';
    EXEC tSQLt.FakeTable 'dbo.OrderItems';

    INSERT INTO dbo.Orders (OrderId, CustomerId) VALUES (1, 100);
    INSERT INTO dbo.OrderItems (OrderId, Quantity, UnitPrice)
    VALUES (1, 2, 10.00), (1, 1, 25.00);

    -- Act: call the function/procedure under test
    DECLARE @result DECIMAL(10,2);
    SELECT @result = dbo.CalculateOrderTotal(1);

    -- Assert
    EXEC tSQLt.AssertEquals 45.00, @result;
END;
```

### FakeTable — Isolating Dependencies

`FakeTable` replaces a real table with an empty copy that has no constraints, triggers, or indexes. This lets you insert test data without worrying about foreign keys or check constraints.

```sql
CREATE OR ALTER PROCEDURE [OrderTests].[test cannot insert duplicate order number]
AS
BEGIN
    -- FakeTable removes constraints — use when testing logic, not constraints
    -- For constraint tests, use the real table
    EXEC tSQLt.FakeTable 'dbo.Products';

    INSERT INTO dbo.Products (ProductId, Name, Price) VALUES (1, 'Widget', 9.99);

    -- Assert an exception is thrown when inserting duplicate PK
    -- Use ApplyConstraint to restore specific constraints
    EXEC tSQLt.ApplyConstraint 'dbo.Products', 'PK_Products';

    EXEC tSQLt.ExpectException @ExpectedMessagePattern = '%PRIMARY KEY%';
    INSERT INTO dbo.Products (ProductId, Name, Price) VALUES (1, 'Duplicate', 5.00);
END;
```

### AssertEqualsTable — Comparing Result Sets

```sql
CREATE OR ALTER PROCEDURE [OrderTests].[test GetActiveOrders returns only active]
AS
BEGIN
    EXEC tSQLt.FakeTable 'dbo.Orders';

    INSERT INTO dbo.Orders (OrderId, Status, CustomerId)
    VALUES (1, 'Active', 10), (2, 'Closed', 10), (3, 'Active', 20);

    -- Create expected results table
    CREATE TABLE #Expected (OrderId INT, Status NVARCHAR(20), CustomerId INT);
    INSERT INTO #Expected VALUES (1, 'Active', 10), (3, 'Active', 20);

    -- Create actual results table
    CREATE TABLE #Actual (OrderId INT, Status NVARCHAR(20), CustomerId INT);
    INSERT INTO #Actual
    EXEC dbo.GetActiveOrders;

    EXEC tSQLt.AssertEqualsTable '#Expected', '#Actual';
END;
```

### FakeFunction and SpyProcedure

```sql
-- SpyProcedure captures calls to a dependency without executing it
EXEC tSQLt.SpyProcedure 'dbo.SendEmailNotification';

-- After calling the procedure under test, verify the spy was called
SELECT * FROM dbo.SendEmailNotification_SpyProcedureLog;

-- FakeFunction replaces a function with one that returns a controlled value
EXEC tSQLt.FakeFunction 'dbo.GetCurrentRate', 'OrderTests.FakeGetCurrentRate';
-- FakeGetCurrentRate simply returns a hardcoded value for predictable tests
```

### Running Tests

```sql
-- Run all tests in a class
EXEC tSQLt.Run 'OrderTests';

-- Run a single test
EXEC tSQLt.Run 'OrderTests.[test CalculateOrderTotal returns correct sum]';

-- Run all tests in the database
EXEC tSQLt.RunAll;

-- Get results as XML (for CI/CD pipeline consumption)
EXEC tSQLt.RunAll;
-- tSQLt automatically outputs results in a readable format
-- Use tSQLt.XmlResultFormatter for XML output
EXEC tSQLt.SetTestResultFormatter 'tSQLt.XmlResultFormatter';
EXEC tSQLt.RunAll;
```

---

## Integration Tests

Integration tests verify that components work together correctly, including referential integrity, triggers, and multi-step workflows.

```sql
-- Integration test: full order creation workflow
CREATE OR ALTER PROCEDURE [IntegrationTests].[test full order creation workflow]
AS
BEGIN
    BEGIN TRANSACTION;
    BEGIN TRY
        -- Use real tables (no FakeTable) to test actual constraints/triggers

        DECLARE @CustomerId INT = 9999;
        DECLARE @OrderId INT;

        -- Insert test customer
        INSERT INTO dbo.Customers (CustomerId, Name, Email)
        VALUES (@CustomerId, 'Test Customer', 'test@example.com');

        -- Create order
        EXEC dbo.CreateOrder
            @CustomerId = @CustomerId,
            @ProductId = 1,
            @Quantity = 3,
            @OrderId = @OrderId OUTPUT;

        -- Verify order was created with correct status
        DECLARE @Status NVARCHAR(20);
        SELECT @Status = Status FROM dbo.Orders WHERE OrderId = @OrderId;

        EXEC tSQLt.AssertEquals 'Pending', @Status;

        -- Verify inventory was decremented
        DECLARE @StockAfter INT;
        SELECT @StockAfter = StockQuantity FROM dbo.Products WHERE ProductId = 1;
        -- Assert stock decreased (original stock - 3)
        EXEC tSQLt.AssertNotEquals 0, @StockAfter; -- still positive

    END TRY
    BEGIN CATCH
        ROLLBACK TRANSACTION;
        THROW;
    END CATCH;

    ROLLBACK TRANSACTION; -- Always rollback in tests
END;
```

---

## Static / Reference Data Management

Reference data (lookup tables, configuration values) must be version-controlled alongside schema objects.

### Static Data Scripts Pattern

```sql
-- Pattern 1: MERGE (idempotent, safe to re-run)
MERGE INTO dbo.OrderStatus AS target
USING (VALUES
    (1, 'Pending',   'Order received, awaiting processing'),
    (2, 'Active',    'Order being processed'),
    (3, 'Shipped',   'Order shipped to customer'),
    (4, 'Delivered', 'Order delivered'),
    (5, 'Cancelled', 'Order cancelled')
) AS source (StatusId, StatusName, Description)
ON target.StatusId = source.StatusId
WHEN MATCHED THEN
    UPDATE SET
        target.StatusName  = source.StatusName,
        target.Description = source.Description
WHEN NOT MATCHED BY TARGET THEN
    INSERT (StatusId, StatusName, Description)
    VALUES (source.StatusId, source.StatusName, source.Description)
WHEN NOT MATCHED BY SOURCE THEN
    DELETE; -- Remove rows no longer in source (optional — use carefully)
```

```sql
-- Pattern 2: DELETE + INSERT (simpler, but causes table scans and identity gaps)
DELETE FROM dbo.OrderStatus;
SET IDENTITY_INSERT dbo.OrderStatus ON;
INSERT INTO dbo.OrderStatus (StatusId, StatusName)
VALUES (1, 'Pending'), (2, 'Active'), (3, 'Shipped');
SET IDENTITY_INSERT dbo.OrderStatus OFF;
```

### Source Control Structure for Static Data

```text
project/
├── Schema/
│   ├── Tables/
│   │   ├── dbo.OrderStatus.sql       ← table definition
│   │   └── dbo.Products.sql
├── Data/
│   ├── ReferenceData/
│   │   ├── dbo.OrderStatus.data.sql  ← static data script (MERGE)
│   │   └── dbo.Countries.data.sql
│   └── SeedData/
│       └── dbo.TestProducts.seed.sql ← dev/test seed data only
└── Tests/
    └── OrderTests/
        └── test_CalculateOrderTotal.sql
```

### Post-Deployment Script for Reference Data

```sql
-- PostDeployment.sql (runs after schema deployment)
PRINT 'Loading reference data...';

:r .\Data\ReferenceData\dbo.OrderStatus.data.sql
:r .\Data\ReferenceData\dbo.Countries.data.sql
:r .\Data\ReferenceData\dbo.Currencies.data.sql

PRINT 'Reference data load complete.';
```

---

## Use Cases

- **Unit tests with tSQLt**: Test stored procedures, functions, and views in isolation before deploying to shared environments
- **FakeTable**: Quickly insert test data without worrying about foreign key chains
- **Integration tests**: Validate end-to-end workflows in a staging environment before production deployment
- **MERGE for reference data**: Deploy lookup table data idempotently as part of CI/CD pipelines

---

## Common Issues & Errors

| Issue | Cause | Fix |
| :--- | :--- | :--- |
| `CLR not enabled` | tSQLt requires CLR | ==`EXEC sp_configure 'clr enabled', 1; RECONFIGURE;`== |
| `TRUSTWORTHY must be ON` | tSQLt assembly requirement | `ALTER DATABASE db SET TRUSTWORTHY ON` |
| Test fails with FK violation | FakeTable not used | Add `EXEC tSQLt.FakeTable` for dependency tables |
| MERGE deletes unexpected rows | `WHEN NOT MATCHED BY SOURCE THEN DELETE` | Remove the DELETE clause if partial updates are intended |
| Test data leaks between tests | Missing ROLLBACK | Wrap integration tests in `BEGIN TRAN / ROLLBACK` |

---

## Exam Tips

> [!tip] Exam Tips
> - tSQLt tests are stored procedures inside a schema with the `tSQLt.TestClass` extended property — no separate test runner binary
> - `FakeTable` removes ALL constraints by default; use `ApplyConstraint` to restore specific ones for constraint testing
> - `MERGE` is the recommended pattern for reference data because it is idempotent (safe to run repeatedly)
> - Post-deployment scripts in dacpac projects run after all schema changes are applied — the right place for reference data loads
> - `tSQLt.AssertEqualsTable` compares entire result sets — use for output of stored procedures returning rowsets

---

## Key Takeaways

- Unit tests isolate database objects using `FakeTable` and `SpyProcedure` — test logic, not data
- Integration tests use real tables and transactions to verify end-to-end behavior
- Static/reference data belongs in source control as idempotent MERGE scripts
- Post-deployment scripts in SQL Database Projects are the standard deployment location for reference data

---

## Related Topics

- [02-SQL Database Projects](./02-sql-database-projects.md)
- [03-Source Control & Branching](./03-source-control-branching.md)
- [04-Deployment Pipelines](./04-deployment-pipelines.md)

---

## Official Documentation

- [tSQLt Framework](https://tsqlt.org/full-user-guide/)
- [MERGE (T-SQL)](https://learn.microsoft.com/en-us/sql/t-sql/statements/merge-transact-sql)
- [SQL Database Projects - Post-Deployment Scripts](https://learn.microsoft.com/en-us/azure/azure-sql/database/sql-projects-overview)

---

**[↑ Back to Section](./README.md) | [Next →](./02-sql-database-projects.md)**
