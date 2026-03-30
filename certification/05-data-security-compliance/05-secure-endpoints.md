---
title: Securing Model, GraphQL, REST, and MCP Endpoints
type: study-material
tags:
  - dp-800
  - managed-identity
  - graphql-security
  - rest-security
  - mcp-security
  - endpoint-security
---

# Securing Model, GraphQL, REST, and MCP Endpoints

## Overview

AI-enabled database solutions expose multiple endpoint types: AI model endpoints, REST APIs (via Data API Builder), GraphQL endpoints, and MCP servers. Each must be secured appropriately using Managed Identity, API authentication, and network controls.

## Securing AI Model Endpoints

### Using Managed Identity to Call Azure OpenAI

```sql
-- sp_invoke_external_rest_endpoint with Managed Identity
EXEC sp_invoke_external_rest_endpoint
    @url = 'https://myopenai.openai.azure.com/openai/deployments/gpt-4o/chat/completions?api-version=2024-02-01',
    @method = 'POST',
    @credential = [https://myopenai.openai.azure.com],  -- DATABASE SCOPED CREDENTIAL
    @payload = N'{"messages":[{"role":"user","content":"Hello"}]}',
    @response = @response OUTPUT;
```

### Creating a Database Scoped Credential for Managed Identity

```sql
-- Grant the SQL database's Managed Identity access to Azure OpenAI in Azure portal first
-- Then create the credential:
CREATE DATABASE SCOPED CREDENTIAL [https://myopenai.openai.azure.com]
WITH IDENTITY = 'Managed Identity';
```

### API Key Authentication (alternative)

```sql
-- Store API key in a credential (less secure than Managed Identity)
CREATE DATABASE SCOPED CREDENTIAL [AzureOpenAIKey]
WITH IDENTITY = 'HTTPEndpointHeaders',
SECRET = '{"api-key":"your-api-key-here"}';
```

## Securing Data API Builder (REST and GraphQL)

### Authentication Configuration

```json
// dab-config.json — authentication section
{
    "runtime": {
        "rest": { "enabled": true },
        "graphql": { "enabled": true },
        "host": {
            "authentication": {
                "provider": "StaticWebApps"
            }
        }
    }
}
```

**Authentication providers for DAB:**
| Provider | Use Case |
| :--- | :--- |
| `StaticWebApps` | Azure Static Web Apps (built-in auth) |
| `AzureAD` | Azure Active Directory / Entra ID |
| `Simulator` | Development and testing only |
| `Anonymous` | Public data (no auth required) |

### Role-Based Access in DAB

```json
// Restrict entity access by role
{
    "entities": {
        "Order": {
            "permissions": [
                {
                    "role": "authenticated",
                    "actions": ["read"]
                },
                {
                    "role": "admin",
                    "actions": ["create", "read", "update", "delete"]
                }
            ]
        }
    }
}
```

### GraphQL-Specific Security

```graphql
# GraphQL introspection should be disabled in production
# dab-config.json: "graphql": { "allow-introspection": false }

# Depth limiting prevents deeply nested queries (DoS)
# "graphql": { "depth-limit": 4 }
```

## Securing MCP Endpoints

MCP servers expose database schema and query capabilities — secure them like any database connection:

```json
// Secure MCP configuration using Managed Identity
{
    "servers": {
        "sql-secure": {
            "type": "stdio",
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-mssql"],
            "env": {
                "MSSQL_CONNECTION_STRING": "Server=myserver.database.windows.net;Database=mydb;Authentication=ActiveDirectoryManagedIdentity;"
            }
        }
    }
}
```

**MCP security principles:**
1. Use Managed Identity — never username/password
2. Create a read-only MCP service account with minimal schema permissions
3. Exclude sensitive tables from MCP visibility (`DENY SELECT`)
4. Use Private Link or service endpoints to restrict network access
5. Enable audit logging on the MCP service account's activities

## Network Security for Endpoints

```text
Azure SQL → Networking tab:
├── Public endpoint: Disable or restrict to known IPs
├── Private endpoint: Use for production (no public internet)
├── Service endpoints: VNet-to-service without public IP
└── Firewall rules: Allow only specific IPs/VNets
```

### Private Endpoint vs Service Endpoint

| Feature | Private Endpoint | Service Endpoint |
| :--- | :--- | :--- |
| Traffic path | Stays on Azure backbone | Optimized route, exits VNet |
| IP type | Private IP in your VNet | Public IP of service |
| DNS | Private DNS zone required | No DNS change |
| Cost | Per-hour + data | No additional cost |
| Recommended | **Yes, for production** | Development/testing |

## Use Cases

- **Managed Identity**: App Services, Azure Functions, and DAB calling Azure SQL and Azure OpenAI
- **DAB with AAD**: Enterprise internal apps where users authenticate with corporate identity
- **Private Link**: Production databases that must never be accessible over the public internet

## Exam Tips

- `DATABASE SCOPED CREDENTIAL` with `IDENTITY = 'Managed Identity'` is the correct syntax for passwordless model calls
- DAB `permissions` array maps roles to allowed CRUD actions per entity
- Disable GraphQL introspection in production to prevent schema discovery
- Private Endpoint = private IP in your VNet; Service Endpoint = optimized route but still public IP

## Key Takeaways

- Use Managed Identity for all service-to-service authentication (model endpoints, DAB, MCP)
- Database Scoped Credential stores the identity reference for `sp_invoke_external_rest_endpoint`
- Restrict network access to endpoints with Private Link or firewall rules

## Related Topics

- [03-Permissions & Access](./03-permissions-access.md)
- [01-Data API Builder](../08-azure-services-integration/01-data-api-builder.md)
- [03-MCP Server Endpoints](../04-ai-assisted-tools/03-mcp-server-endpoints.md)

## Official Documentation

- [Managed Identity for SQL Database](https://learn.microsoft.com/en-us/azure/azure-sql/database/authentication-azure-ad-user-assigned-managed-identity)
- [DAB Authentication](https://learn.microsoft.com/en-us/azure/data-api-builder/authentication-azure-ad)
- [Database Scoped Credentials](https://learn.microsoft.com/en-us/sql/t-sql/statements/create-database-scoped-credential-transact-sql)

---

**[← Previous](./04-auditing.md) | [↑ Back to Section](./README.md)**
