---
title: Data API Builder (DAB)
type: study-material
tags:
  - dp-800
  - data-api-builder
  - dab
  - rest
  - graphql
---

# Data API Builder (DAB)

## Overview

Data API Builder (DAB) is an open-source tool from Microsoft that automatically generates REST and GraphQL APIs from database objects (tables, views, stored procedures) without writing any API code. DAB reads a configuration file (`dab-config.json`) that defines data sources, entity mappings, security, and behavior — then exposes the configured endpoints.

DAB supports Azure SQL, SQL Server, Azure Cosmos DB, and MySQL/PostgreSQL, and can be deployed as a container or hosted in Azure Static Web Apps or Azure App Service.

## DAB Configuration File Structure

The `dab-config.json` file controls everything DAB does:

```json
{
  "$schema": "https://github.com/Azure/data-api-builder/releases/download/v1.1.7/dab.draft.schema.json",
  "data-source": {
    "database-type": "mssql",
    "connection-string": "@env('DATABASE_CONNECTION_STRING')",
    "options": {
      "set-session-context": true
    }
  },
  "runtime": {
    "rest": {
      "enabled": true,
      "path": "/api",
      "request-body-strict": true
    },
    "graphql": {
      "enabled": true,
      "path": "/graphql",
      "allow-introspection": true
    },
    "host": {
      "mode": "production",
      "cors": {
        "origins": ["https://myapp.azurewebsites.net"],
        "allow-credentials": true
      },
      "authentication": {
        "provider": "AzureAD",
        "jwt": {
          "audience": "api://my-app-id",
          "issuer": "https://login.microsoftonline.com/{tenant}/v2.0"
        }
      }
    }
  },
  "entities": {
    "Order": {
      "source": {
        "object": "dbo.Orders",
        "type": "table",
        "key-fields": ["OrderId"]
      },
      "rest": {
        "enabled": true,
        "methods": ["get", "post", "put", "patch", "delete"]
      },
      "graphql": {
        "enabled": true,
        "type": {
          "singular": "Order",
          "plural": "Orders"
        }
      },
      "permissions": [
        {
          "role": "authenticated",
          "actions": ["read", "create", "update"]
        },
        {
          "role": "anonymous",
          "actions": ["read"]
        }
      ]
    }
  }
}
```

## Data Sources

DAB supports a single primary data source per runtime instance:

```json
{
  "data-source": {
    "database-type": "mssql",
    "connection-string": "@env('DATABASE_CONNECTION_STRING')",
    "options": {
      "set-session-context": true
    }
  }
}
```

The connection string should **never** be hardcoded — use `@env('VAR_NAME')` to reference environment variables or Azure Key Vault references.

For SQL Database in Fabric (or Azure SQL), use a connection string like:
```text
Server=myserver.database.windows.net;Database=MyDB;Authentication=Active Directory Default;
```

## Entity Configuration

### Table Entity

```json
"Product": {
  "source": {
    "object": "dbo.Products",
    "type": "table",
    "key-fields": ["ProductId"]
  },
  "mappings": {
    "ProductId": "id",
    "ProductName": "name",
    "UnitPrice": "price"
  },
  "rest": { "enabled": true },
  "graphql": { "enabled": true },
  "permissions": [
    { "role": "authenticated", "actions": ["read"] }
  ]
}
```

`mappings` renames database columns to API field names (e.g., `ProductName` becomes `name` in the API response).

### View Entity (Read-Only)

```json
"ActiveOrders": {
  "source": {
    "object": "dbo.vw_ActiveOrders",
    "type": "view",
    "key-fields": ["OrderId"]
  },
  "rest": {
    "enabled": true,
    "methods": ["get"]
  },
  "graphql": { "enabled": true },
  "permissions": [
    { "role": "authenticated", "actions": ["read"] }
  ]
}
```

### Stored Procedure Entity

```json
"CreateOrder": {
  "source": {
    "object": "dbo.CreateOrder",
    "type": "stored-procedure",
    "parameters": {
      "CustomerId": "number",
      "ProductId": "number",
      "Quantity": "number"
    }
  },
  "rest": {
    "enabled": true,
    "methods": ["post"]
  },
  "graphql": {
    "enabled": true,
    "operation": "mutation"
  },
  "permissions": [
    { "role": "authenticated", "actions": ["execute"] }
  ]
}
```

## Relationships

DAB can express relationships between entities for GraphQL nested queries:

```json
"Order": {
  "source": { "object": "dbo.Orders", "type": "table", "key-fields": ["OrderId"] },
  "relationships": {
    "items": {
      "target.entity": "OrderItem",
      "source.fields": ["OrderId"],
      "target.fields": ["OrderId"],
      "cardinality": "many"
    },
    "customer": {
      "target.entity": "Customer",
      "source.fields": ["CustomerId"],
      "target.fields": ["CustomerId"],
      "cardinality": "one"
    }
  }
}
```

This enables GraphQL queries like:
```graphql
query {
  orders {
    items {
      orderId
      items {
        productId
        quantity
      }
      customer {
        name
        email
      }
    }
  }
}
```

## Pagination, Caching, and Filtering

### Pagination

DAB supports cursor-based pagination automatically. REST responses include a `nextLink` for the next page:

```json
{
  "runtime": {
    "pagination": {
      "default-page-size": 20,
      "max-page-size": 100
    }
  }
}
```

REST pagination:
```text
GET /api/Order?$first=20           → first 20 rows
GET /api/Order?$first=20&$after=eyJ... → next page using cursor
```

### Caching

```json
{
  "runtime": {
    "cache": {
      "enabled": true,
      "ttl-seconds": 300
    }
  }
}
```

Caching can also be configured per-entity to override the global setting.

### Filtering and Searching

DAB supports OData-style filter expressions for REST:

```text
# Filter by field value
GET /api/Order?$filter=Status eq 'Active'

# Multiple conditions
GET /api/Order?$filter=Status eq 'Active' and CustomerId eq 42

# Order by
GET /api/Order?$orderby=OrderDate desc

# Select specific fields
GET /api/Order?$select=OrderId,CustomerId,Status

# Search (requires full-text index on the table)
GET /api/Product?$search=laptop
```

## DAB CLI Commands

```bash
# Install DAB CLI
dotnet tool install -g Microsoft.DataApiBuilder

# Initialize a new configuration file
dab init --database-type mssql \
         --connection-string "@env('DATABASE_CONNECTION_STRING')" \
         --config dab-config.json

# Add an entity (table)
dab add Product \
    --source dbo.Products \
    --permissions "anonymous:read" \
    --config dab-config.json

# Add a stored procedure entity
dab add CreateOrder \
    --source dbo.CreateOrder \
    --source.type stored-procedure \
    --permissions "authenticated:execute" \
    --config dab-config.json

# Start DAB locally for development
dab start --config dab-config.json

# Validate configuration
dab validate --config dab-config.json
```

## Deployment

### Container Deployment

```bash
# Pull the DAB container image
docker pull mcr.microsoft.com/azure-databases/data-api-builder:latest

# Run locally
docker run -p 5000:5000 \
    -e DATABASE_CONNECTION_STRING="Server=...;Authentication=Active Directory Default" \
    -v $(pwd)/dab-config.json:/App/dab-config.json \
    mcr.microsoft.com/azure-databases/data-api-builder:latest
```

### Azure Static Web Apps (Integrated)

DAB is natively integrated into Azure Static Web Apps as a "linked backend" — no separate hosting needed. Configure in `staticwebapp.config.json` and `swa-db-connections/` folder.

### Azure App Service / Container Apps

```yaml
# Azure Container Apps deployment example
az containerapp create \
  --name my-dab-api \
  --resource-group myRG \
  --environment myEnv \
  --image mcr.microsoft.com/azure-databases/data-api-builder:latest \
  --secrets "connection-string=keyvaultref:..." \
  --env-vars "DATABASE_CONNECTION_STRING=secretref:connection-string"
```

## Use Cases

- **Rapid API development**: Expose an Azure SQL database as a REST/GraphQL API with zero custom code
- **Fabric SQL database**: Enable web and mobile apps to query SQL Database in Fabric via a standard API
- **Static Web Apps backend**: DAB as a managed data API backend for SPA applications
- **Stored procedure exposure**: Expose complex business logic as API operations

## Common Issues & Errors

| Issue | Cause | Fix |
| :--- | :--- | :--- |
| `Anonymous access denied` | Permission not set for anonymous role | Add `"role": "anonymous", "actions": ["read"]` to entity permissions |
| `Key field not found` | `key-fields` doesn't match column name | Verify column name matches exactly; check `mappings` if renamed |
| `Stored procedure parameter type mismatch` | Wrong type in `parameters` config | Use `"number"` for INT, `"string"` for VARCHAR |
| Connection string in config file | Security risk | Use `@env('VAR_NAME')` to reference environment variables |
| GraphQL introspection disabled in prod | `allow-introspection: false` | Set to `true` only in dev; keep `false` in production for security |

## Exam Tips

- DAB config uses `@env('VAR_NAME')` for connection strings — never hardcode credentials
- Entities map to tables, views, or stored procedures — the `type` field controls this
- REST methods are configured per-entity; stored procedures default to `post` for mutations
- `mappings` rename database column names to API field names without changing the database
- Relationships in DAB enable nested GraphQL queries — defined by source/target fields and cardinality

## Key Takeaways

- DAB generates REST and GraphQL APIs from SQL objects using a single JSON config file
- Security is configured per-entity with roles (anonymous, authenticated, custom) and allowed actions
- The DAB CLI (`dab init`, `dab add`, `dab start`) is the primary development workflow
- DAB supports pagination, filtering, caching, and relationships out of the box

## Related Topics

- [02-REST & GraphQL Endpoints](./02-rest-graphql-endpoints.md)
- [03-Monitoring](./03-monitoring.md)

## Official Documentation

- [Data API Builder Overview](https://learn.microsoft.com/en-us/azure/data-api-builder/overview-to-data-api-builder)
- [DAB Configuration Reference](https://learn.microsoft.com/en-us/azure/data-api-builder/configuration-file)
- [DAB CLI Reference](https://learn.microsoft.com/en-us/azure/data-api-builder/data-api-builder-cli)

---

**[↑ Back to Section](./README.md) | [Next →](./02-rest-graphql-endpoints.md)**
