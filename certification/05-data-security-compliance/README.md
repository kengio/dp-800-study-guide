---
title: Implement Data Security and Compliance
type: category
tags:
  - dp-800
  - security
  - encryption
  - rls
  - dynamic-data-masking
  - auditing
status: draft
---

# Implement Data Security and Compliance (Domain 2 — 35–40%)

Securing SQL database solutions through encryption, data masking, row-level security, permission management, and auditing.

---

## Quick Recall

```mermaid
mindmap
  root((Security))
    Encryption
      TDE - at rest transparent
      Always Encrypted - in memory
      Column-level - manual
    Masking and RLS
      DDM - hide values not encrypt
      RLS - filter/block rows
    Permissions
      DENY overrides GRANT
      REVOKE removes not denies
      Fixed roles
    Auditing
      Storage/Log Analytics/Event Hub
      sys.fn_get_audit_file
```

---

## Topics Overview

```mermaid
flowchart TD
    SEC[Data Security] --> Encryption[Encryption]
    SEC --> Masking[Dynamic Data Masking & RLS]
    SEC --> Perms[Permissions & Access]
    SEC --> Audit[Auditing]
    SEC --> Endpoints[Secure Endpoints]
    Encryption --> AE[Always Encrypted]
    Encryption --> ColEnc[Column-Level Encryption]
```

## Section Contents

| File | Topic | Priority |
| :--- | :--- | :--- |
| [01-encryption.md](01-encryption.md) | Always Encrypted, column-level encryption | High |
| [02-dynamic-data-masking-rls.md](02-dynamic-data-masking-rls.md) | Dynamic Data Masking and Row-Level Security | High |
| [03-permissions-access.md](03-permissions-access.md) | Object-level permissions, passwordless access | High |
| [04-auditing.md](04-auditing.md) | Database and server auditing | Medium |
| [05-secure-endpoints.md](05-secure-endpoints.md) | Managed Identity, GraphQL/REST/MCP endpoint security | Medium |

## Key Concepts

- **Always Encrypted**: Client-side encryption — server never sees plaintext; uses column master keys
- **Column-Level Encryption**: Server-side using certificates or asymmetric keys
- **Dynamic Data Masking (DDM)**: Obscures sensitive data in query results without changing stored data
- **Row-Level Security (RLS)**: Inline table-valued function predicates control row visibility per user
- **Managed Identity**: Passwordless authentication to Azure services
- **Auditing**: Track database events to storage account, Event Hub, or Log Analytics

## Related Resources

- [04-AI-Assisted Tools](../04-ai-assisted-tools/README.md)
- [06-Performance Optimization](../06-performance-optimization/README.md)
- [Official: Always Encrypted](https://learn.microsoft.com/en-us/sql/relational-databases/security/encryption/always-encrypted-database-engine)

## Next Steps

Proceed to [06-Performance Optimization](../06-performance-optimization/README.md) to learn about query tuning and performance monitoring.

---

**[← Back to AI-Assisted Tools](../04-ai-assisted-tools/README.md) | [↑ Back to Certification](../README.md)**
