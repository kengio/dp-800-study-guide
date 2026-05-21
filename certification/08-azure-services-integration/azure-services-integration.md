---
title: Integrate SQL Solutions with Azure Services
type: category
tags:
  - dp-800
  - azure
  - data-api-builder
  - rest
  - graphql
  - cdc
  - azure-monitor
status: complete
---

# Integrate SQL Solutions with Azure Services (Domain 2 — 35–40%)

Integrating SQL databases with Azure services including Data API Builder (DAB), REST/GraphQL endpoints, monitoring with Azure Monitor, and change event handling.

---

## Quick Recall

```mermaid
mindmap
  root((Azure Integration))
    DAB
      Config file only no code
      REST /api/Entity
      GraphQL /graphql
    Monitoring
      Azure Monitor metrics
      DMVs - engine diagnostics
      Query Store - plan regression
    Change Tracking
      CDC - before/after values needs Agent
      CT - row changed only no Agent
    Network
      Private endpoint - private IP
      Service endpoint - routing only
```

---

## Topics Overview

```mermaid
flowchart TD
    Azure[Azure Integration] --> DAB[Data API Builder]
    Azure --> Endpoints[REST & GraphQL Endpoints]
    Azure --> Monitor[Monitoring]
    Azure --> Changes[Change Event Handling]
    DAB --> Entities[Entities Config]
    DAB --> Deploy[DAB Deployment]
    Changes --> CDC[CDC]
    Changes --> CES[CES]
    Changes --> AzFunc[Azure Functions]
```

## Section Contents

| File | Topic | Priority |
| :--- | :--- | :--- |
| [01-data-api-builder.md](01-data-api-builder.md) | DAB configuration, entities, REST/GraphQL | High |
| [02-rest-graphql-endpoints.md](02-rest-graphql-endpoints.md) | Endpoint config, pagination, caching, filtering | High |
| [03-monitoring.md](03-monitoring.md) | Azure Monitor, Application Insights, Log Analytics | Medium |
| [04-change-event-handling.md](04-change-event-handling.md) | CDC, CES, Change Tracking, Azure Functions, Logic Apps | High |

## Key Concepts

- **Data API Builder (DAB)**: Open-source tool that generates REST and GraphQL APIs from database objects
- **DAB Configuration**: `dab-config.json` defines data sources, entities, authentication, and caching
- **GraphQL Relationships**: DAB exposes foreign key relationships as nested GraphQL types
- **Change Data Capture (CDC)**: Captures row-level changes in SQL Server/Azure SQL at the transaction log level
- **Change Event Streaming (CES)**: Near-real-time event stream from SQL databases in Fabric
- **Azure Functions SQL Trigger Binding**: Triggers a function on data changes using CDC under the hood

## Related Resources

- [07-CI/CD Database Projects](../07-cicd-database-projects/cicd-database-projects.md)
- [09-Models & Embeddings](../09-models-embeddings/models-embeddings.md)
- [Official: Data API Builder](https://learn.microsoft.com/en-us/azure/data-api-builder/overview-to-data-api-builder)

## Next Steps

Proceed to [09-Models & Embeddings](../09-models-embeddings/models-embeddings.md) to start exploring AI capabilities.

---

**[← Back to CI/CD Database Projects](../07-cicd-database-projects/cicd-database-projects.md) | [↑ Back to Certification](../dp-800-overview.md)**
