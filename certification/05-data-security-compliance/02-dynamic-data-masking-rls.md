---
title: Dynamic Data Masking and Row-Level Security
type: study-material
tags:
  - dp-800
  - dynamic-data-masking
  - row-level-security
  - rls
  - ddm
---

# Dynamic Data Masking and Row-Level Security

## Overview

**Dynamic Data Masking** (DDM) obfuscates sensitive column values for unauthorized users without changing stored data. Row-Level Security (RLS) controls which rows a user can access based on a security predicate function.

> [!abstract]
> - Covers Dynamic Data Masking (DDM) and Row-Level Security (RLS) — two complementary data access control features
> - DDM hides column values; RLS hides entire rows — both are transparent to the application
> - Key exam topics: DDM mask types, DDM limitations, RLS predicate function creation, filter vs block predicates

> [!tip] What the Exam Tests
> - **DDM**: hides values at query time; does NOT encrypt; privileged users with `UNMASK` see everything; four mask types: `default()`, `email()`, `partial()`, `random()`
> - **RLS**: `CREATE SECURITY POLICY` attaches a predicate function to a table; **filter predicate** = limits SELECT; **block predicate** = prevents DML that violates the policy
> - RLS is completely transparent — the filtered user gets fewer rows with no indication rows are missing

---

## Dynamic Data Masking (DDM)

DDM applies masking rules to columns — users without the `UNMASK` permission see obfuscated values.

### Masking Functions

| Function | Syntax | Example Output |
| :--- | :--- | :--- |
| **default()** | `MASKED WITH (FUNCTION = 'default()')` | `xxxx` for strings, `0` for numbers, `01/01/1900` for dates |
| **email()** | `MASKED WITH (FUNCTION = 'email()')` | `aXXX@XXXX.com` |
| **random(m,n)** | `MASKED WITH (FUNCTION = 'random(1,100)')` | Random number in range |
| **partial(p,s,l)** | `MASKED WITH (FUNCTION = 'partial(2,"XXXX",2)')` | `14XXXX42` |
| **datetime(format)** | `MASKED WITH (FUNCTION = 'datetime("Y-M-D")')` | Partial date reveal |

### Adding DDM to Columns

```sql
-- Add masking when creating a table
CREATE TABLE dbo.Customers (
    CustomerId  int             NOT NULL PRIMARY KEY,
    Name        nvarchar(100)   NOT NULL,
    Email       nvarchar(200)   MASKED WITH (FUNCTION = 'email()'),
    Phone       varchar(20)     MASKED WITH (FUNCTION = 'partial(0,"XXX-XXX-",4)'),
    CreditLimit money           MASKED WITH (FUNCTION = 'default()')
);

-- Add masking to an existing column
ALTER TABLE dbo.Customers
ALTER COLUMN SSN char(11)
MASKED WITH (FUNCTION = 'partial(0,"XXX-XX-",4)');

-- Remove masking
ALTER TABLE dbo.Customers
ALTER COLUMN SSN char(11) DROP MASKED;
```

### Permissions

```sql
-- Users with db_owner or UNMASK permission see real values
-- Grant unmask to trusted users
GRANT UNMASK ON dbo.Customers TO [AnalystUser];

-- Grant column-level unmask (SQL 2022+)
GRANT UNMASK ON dbo.Customers(Email) TO [MarketingUser];

-- Check masked columns
SELECT * FROM sys.masked_columns;
```

> Important: DDM does NOT prevent inference attacks — a user can guess values through repeated queries. For true data protection, use Always Encrypted.

> [!warning] Common Mistake
> DDM is NOT a security boundary for privileged users. Any user with `SELECT` permission AND `UNMASK` permission sees the real data. DDM is a usability feature, not an encryption feature. For true data protection, use Always Encrypted or column-level encryption.

---

## Row-Level Security (RLS)

RLS controls which rows are returned to a user based on a filter predicate defined as an inline table-valued function.

### RLS Architecture

```text
User query → Security predicate function → Filtered rows returned
```

### Implementing Filter Predicate

```sql
-- Step 1: Create the predicate function
CREATE FUNCTION Security.fn_OrderFilter (
    @CustomerId int
)
RETURNS TABLE
WITH SCHEMABINDING
AS
RETURN
(
    SELECT 1 AS fn_result
    WHERE
        -- Admin sees all rows
        USER_NAME() = 'dbo'
        OR
        -- Customer sees only their own orders
        @CustomerId = CAST(SESSION_CONTEXT(N'CustomerId') AS int)
);
GO

-- Step 2: Create the security policy
CREATE SECURITY POLICY OrderFilterPolicy
ADD FILTER PREDICATE Security.fn_OrderFilter(CustomerId)
ON dbo.Orders
WITH (STATE = ON);
```

### Block Predicates

Block predicates prevent INSERT/UPDATE/DELETE that would create rows the user cannot see:

```sql
CREATE SECURITY POLICY SalesRepPolicy
ADD FILTER PREDICATE Security.fn_SalesRepFilter(SalesRepId)
    ON dbo.Opportunities,
ADD BLOCK PREDICATE Security.fn_SalesRepFilter(SalesRepId)
    ON dbo.Opportunities AFTER INSERT,
ADD BLOCK PREDICATE Security.fn_SalesRepFilter(SalesRepId)
    ON dbo.Opportunities AFTER UPDATE
WITH (STATE = ON);
```

**Predicate types:**

| Type                  | Applies To             | Blocks                                |
| :-------------------- | :--------------------- | :------------------------------------ |
| `FILTER`              | SELECT, UPDATE, DELETE | ==Invisible rows (not an error)==     |
| `BLOCK AFTER INSERT`  | INSERT                 | Inserts that would be invisible       |
| `BLOCK AFTER UPDATE`  | UPDATE                 | Updates that result in invisible rows |
| `BLOCK BEFORE UPDATE` | UPDATE                 | Updates on currently invisible rows   |
| `BLOCK BEFORE DELETE` | DELETE                 | Deletes on currently invisible rows   |

### Using SESSION_CONTEXT for Multi-Tenant RLS

```sql
-- Set context on connection (from application layer)
EXEC sp_set_session_context @key = N'TenantId', @value = 42, @read_only = 1;

-- Predicate reads the context
CREATE FUNCTION Security.fn_TenantFilter (@TenantId int)
RETURNS TABLE WITH SCHEMABINDING AS
RETURN (
    SELECT 1 AS fn_result
    WHERE @TenantId = CAST(SESSION_CONTEXT(N'TenantId') AS int)
        OR IS_MEMBER('db_owner') = 1
);
```

### Managing RLS Policies

```sql
-- Disable policy temporarily
ALTER SECURITY POLICY OrderFilterPolicy WITH (STATE = OFF);

-- Enable policy
ALTER SECURITY POLICY OrderFilterPolicy WITH (STATE = ON);

-- Drop policy
DROP SECURITY POLICY OrderFilterPolicy;

-- View policies
SELECT * FROM sys.security_policies;
SELECT * FROM sys.security_predicates;
```

---

## DDM vs RLS Comparison

| Aspect | Dynamic Data Masking | Row-Level Security |
| :--- | :--- | :--- |
| **Hides what** | Column values | Entire rows |
| **User sees** | Masked value (row still returned) | Row not returned at all |
| **Prevents inference** | No | Yes |
| **Implementation** | Column attribute | Inline TVF + security policy |
| **Impact on performance** | Minimal | Small overhead per query |
| **Best for** | Data display protection | ==Multi-tenant isolation== |

---

## Use Cases

- **DDM**: Customer support apps — mask PII for agents; developers working on production data copies
- **RLS Filter**: Multi-tenant SaaS — each tenant sees only their rows
- **RLS Block**: Prevent users from inserting rows for other tenants

---

## Common Issues & Errors

| Issue | Cause | Resolution |
| :--- | :--- | :--- |
| RLS predicate not working | Function doesn't return 1 for valid rows | Test the function directly with `SELECT * FROM Security.fn_Filter(value)` |
| Infinite recursion in predicate | Predicate queries the protected table | Use a separate security table; never query the filtered table inside the predicate |
| DDM bypassed | User has UNMASK permission or is db_owner | Review permission grants; DDM doesn't protect from owners |

---

## Exam Tips

> [!tip] Exam Tips
> - DDM masks values but **doesn't prevent access** — determined users can infer data
> - RLS uses inline TVFs with `SCHEMABINDING` — always use `WITH SCHEMABINDING`
> - `SESSION_CONTEXT` is the recommended pattern for passing tenant context to RLS
> - RLS `FILTER` predicates are applied to SELECT/UPDATE/DELETE; `BLOCK` predicates prevent writes

---

## Key Takeaways

- DDM = column-value obfuscation (presentation layer protection)
- RLS = row-level access control (data isolation)
- Combine DDM + RLS for comprehensive data protection in multi-tenant apps

---

## Related Topics

- [01-Encryption](./01-encryption.md)
- [03-Permissions & Access](./03-permissions-access.md)

---

## Official Documentation

- [Dynamic Data Masking](https://learn.microsoft.com/en-us/sql/relational-databases/security/dynamic-data-masking)
- [Row-Level Security (SQL Server)](https://learn.microsoft.com/en-us/sql/relational-databases/security/row-level-security)

---

**[← Previous](./01-encryption.md) | [↑ Back to Section](./data-security-compliance.md) | [Next →](./03-permissions-access.md)**
