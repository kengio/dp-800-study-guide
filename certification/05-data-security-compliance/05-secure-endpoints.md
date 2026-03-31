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

> [!abstract]
> - Covers network security for Azure SQL: firewall rules, private endpoints, service endpoints, and authentication
> - Network access and authentication are layered — both must be correct for a connection to succeed
> - Key exam topics: private endpoint vs service endpoint differences, Azure AD authentication vs SQL auth, managed identity

> [!tip] What the Exam Tests
> - **Private endpoint**: assigns a private IP in your VNet; traffic never leaves Azure network; the SQL endpoint is no longer publicly reachable
> - **Service endpoint**: routes traffic via Azure backbone; endpoint is still a public IP — it's a routing optimization, not full privatization
> - **Managed identity**: no passwords or connection strings; Azure AD token auth; system-assigned (per resource) vs user-assigned (shared)

---

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

## Private Endpoints vs Service Endpoints

- **Service Endpoint**: extends VNet identity to Azure SQL — traffic stays on Azure backbone, public IP not required, but the SQL server still has a public-facing endpoint accessible from the internet
- **Private Endpoint**: assigns a private IP from your VNet — SQL server is not reachable from the public internet at all; powered by Azure Private Link

| Feature | Service Endpoint | Private Endpoint |
| :--- | :--- | :--- |
| SQL has public IP | Still accessible publicly | No public access (if disabled) |
| VNet integration | Traffic via backbone | Private IP in VNet |
| Cross-region | Limited | Yes (via Private Link) |
| Cost | Free | Requires Private Link pricing |
| Exam preferred option | Legacy approach | Modern/recommended |

> [!warning] Common Mistake
> Private endpoint and service endpoint sound similar but work differently. Service endpoint = your VNet traffic stays on Azure backbone, but the SQL Server endpoint is still a public IP (reachable from the internet if firewall allows). Private endpoint = SQL Server gets a private IP in your VNet — fully private, not publicly routable.

## Firewall Rules for Azure SQL

Azure SQL supports multiple firewall rule layers:

- **Server-level firewall rules**: apply to all databases on the logical server; configured in the Azure portal or via T-SQL master
- **Database-level firewall rules** (`sp_set_database_firewall_rule`): override server-level rules for a specific database; set by users with appropriate permissions
- **Allow Azure services rule**: the "Allow access to Azure services" toggle adds a `0.0.0.0` rule — permits any Azure-hosted service, including other tenants; use with caution
- **Virtual network rules**: restrict access to specific VNet subnets; require service endpoints enabled on the subnet

```sql
-- Create database-level firewall rule
EXEC sp_set_database_firewall_rule
    @name = N'DevMachine',
    @start_ip_address = '203.0.113.0',
    @end_ip_address = '203.0.113.0';

-- View current database firewall rules
SELECT * FROM sys.database_firewall_rules;

-- Remove a rule
EXEC sp_delete_database_firewall_rule @name = N'DevMachine';
```

## Managed Identity for Service-to-Service

Managed Identity eliminates the need to store or rotate credentials for service-to-service connections.

**System-assigned vs user-assigned:**

- **System-assigned**: tied to a single resource lifecycle; auto-deleted when the resource is deleted
- **User-assigned**: standalone Azure resource; shareable across multiple services

**Using Managed Identity from App Service, Azure Functions, or Logic Apps to Azure SQL:**

1. Enable Managed Identity on the calling service (Azure portal)
2. Add the identity as an Azure AD user in the target database
3. Grant appropriate roles
4. Use a passwordless connection string

```sql
-- Allow a Managed Identity to access the database
-- (run as Azure AD admin)
CREATE USER [my-function-app] FROM EXTERNAL PROVIDER;
ALTER ROLE db_datareader ADD MEMBER [my-function-app];

-- Connection string (no password needed)
-- "Server=myserver.database.windows.net;Authentication=Active Directory Managed Identity;Database=mydb"
```

No credentials to rotate or store — the Azure platform manages token acquisition automatically.

## Transport Encryption (TLS)

- Azure SQL always enforces TLS 1.2+ for data in transit; connections using older TLS versions are rejected
- Set `Encrypt=True` in the connection string to ensure the client enforces encryption (required for all production connections)
- Set `TrustServerCertificate=False` in production — allows the client to validate the server certificate chain rather than blindly trusting it
- Azure SQL uses certificates from the DigiCert Global Root G2 CA; clients must trust this root
- Example connection string with correct encryption settings:

```sql
-- ADO.NET connection string example
-- Server=myserver.database.windows.net;Database=mydb;
-- Authentication=Active Directory Managed Identity;
-- Encrypt=True;TrustServerCertificate=False;
```

## Microsoft Defender for SQL

Microsoft Defender for SQL provides two capabilities under a single plan:

- **Advanced Threat Protection**: detects unusual access patterns, SQL injection attempts, brute-force login attempts, and suspicious data exfiltration activity
- **Vulnerability Assessment**: periodically scans the database for security misconfigurations, excessive permissions, and unpatched issues; produces a baseline and tracks deviations

**Integration:**

- Alerts appear in Microsoft Defender for Cloud (formerly Azure Security Center)
- Alert types include: suspicious IP access, anomalous query patterns, potential data exfiltration, and access from unfamiliar locations
- Enable at the subscription level to cover all SQL resources automatically

## Use Cases

- **Managed Identity**: App Services, Azure Functions, and DAB calling Azure SQL and Azure OpenAI
- **DAB with AAD**: Enterprise internal apps where users authenticate with corporate identity
- **Private Link**: Production databases that must never be accessible over the public internet

## Common Issues & Errors

- **Private endpoint not working**: check that the private DNS zone is linked to the VNet so that the SQL server FQDN resolves to the private IP
- **Managed Identity login fails**: the identity must exist as an Azure AD user in the target database (`CREATE USER ... FROM EXTERNAL PROVIDER`); server-level permissions alone are not enough
- **`0.0.0.0` firewall rule**: the "Allow Azure services" toggle creates this rule — it permits all Azure-hosted services, not just your own; prefer VNet rules instead
- **TLS handshake failure**: older drivers may not support TLS 1.2; upgrade the driver or client SDK

## Best Practices

- Disable the public endpoint on Azure SQL for production workloads and use Private Endpoint exclusively
- Prefer Managed Identity over API keys or SQL authentication for all service-to-service connections
- Use database-level firewall rules for per-database overrides rather than broadening server-level rules
- Enable Microsoft Defender for SQL on all production databases for continuous threat monitoring
- Always set `Encrypt=True;TrustServerCertificate=False` in connection strings to enforce proper TLS validation

## Exam Tips

- `DATABASE SCOPED CREDENTIAL` with `IDENTITY = 'Managed Identity'` is the correct syntax for passwordless model calls
- DAB `permissions` array maps roles to allowed CRUD actions per entity
- Disable GraphQL introspection in production to prevent schema discovery
- Private Endpoint = private IP in your VNet; Service Endpoint = optimized route but still public IP
- `sp_set_database_firewall_rule` targets a single database; server-level rules apply to all databases on the logical server
- `CREATE USER [name] FROM EXTERNAL PROVIDER` is required before a Managed Identity can log in to a specific database

## Key Takeaways

- Use Managed Identity for all service-to-service authentication (model endpoints, DAB, MCP)
- Database Scoped Credential stores the identity reference for `sp_invoke_external_rest_endpoint`
- Restrict network access to endpoints with Private Link or firewall rules
- Private Endpoint is the modern recommended approach; Service Endpoint is legacy and leaves the public endpoint active

## Practice Question

An organization requires that their Azure SQL Database is accessible only from within their Azure virtual network and NOT reachable from the public internet. Which configuration achieves this?

A. Create a server-level firewall rule allowing only the VNet IP range
B. Enable a service endpoint and block all public access rules
C. Create a private endpoint and disable the public endpoint on the SQL server
D. Enable Managed Identity authentication to replace password-based access

> [!success]- Answer
> **C — Create a private endpoint and disable the public endpoint on the SQL server**
>
> A private endpoint assigns a private IP to the SQL server within the VNet and, when combined with disabling the public endpoint, makes the SQL server completely unreachable from the internet. Service endpoints (B) keep the SQL server's public endpoint active — they only route VNet traffic over the Azure backbone. Firewall rules (A) reduce exposure but the server still has a public-facing endpoint. Managed Identity (D) improves authentication security but doesn't change network accessibility.

## Related Topics

- [03-Permissions & Access](./03-permissions-access.md)
- [01-Data API Builder](../08-azure-services-integration/01-data-api-builder.md)
- [03-MCP Server Endpoints](../04-ai-assisted-tools/03-mcp-server-endpoints.md)

## Official Documentation

- [Managed Identity for SQL Database](https://learn.microsoft.com/en-us/azure/azure-sql/database/authentication-azure-ad-user-assigned-managed-identity)
- [DAB Authentication](https://learn.microsoft.com/en-us/azure/data-api-builder/authentication-azure-ad)
- [Database Scoped Credentials](https://learn.microsoft.com/en-us/sql/t-sql/statements/create-database-scoped-credential-transact-sql)
- [Azure SQL Firewall Rules](https://learn.microsoft.com/en-us/azure/azure-sql/database/firewall-configure)
- [Azure Private Link for SQL](https://learn.microsoft.com/en-us/azure/azure-sql/database/private-endpoint-overview)
- [Microsoft Defender for SQL](https://learn.microsoft.com/en-us/azure/azure-sql/database/azure-defender-for-sql)

---

**[← Previous](./04-auditing.md) | [↑ Back to Section](./README.md)**
