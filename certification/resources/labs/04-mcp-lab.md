---
title: MCP Server Lab — Copilot in Fabric + GitHub Copilot
type: lab
tags:
  - dp-800
  - hands-on
  - lab
  - mcp
  - model-context-protocol
  - copilot
status: complete
---

# Lab 04 — MCP Server Endpoints with Copilot

## Overview

Stand up a Model Context Protocol (MCP) server endpoint over the
`Lab01_Products` database, wire it into **GitHub Copilot chat** in VS Code,
and walk through the same configuration steps for **Copilot in Microsoft
Fabric**. The lab focuses on the exam-testable surface: where the config
lives, what the auth options are, what permissions the MCP service account
needs, and what an MCP `call_tool` round-trip looks like.

> [!abstract]
>
> - Configure an MCP server pointing at SQL Server 2025 / Azure SQL via `.vscode/mcp.json`
> - Wire the same endpoint to **Microsoft Foundry** Copilot in Fabric using the hosted Fabric lakehouse MCP URL
> - Authenticate with ==Managed Identity== (preferred) or a least-privilege SQL user
> - Run a chat session that uses MCP to discover schema and write a query against the lab `dbo.Products` catalogue

> [!warning] Preview status
> The Microsoft SQL Server MCP server is **public preview** as of the March 2026
> blueprint; the Fabric lakehouse MCP endpoint is **public preview** in
> selected regions. The configuration steps and security model in this lab are
> stable and testable on the exam even where the runtime is still preview-only.

> [!tip] What you'll do
>
> 1. Create a least-privilege MCP service principal / database user on `Lab01_Products`
> 2. Author a `.vscode/mcp.json` that launches `@modelcontextprotocol/server-mssql` over stdio
> 3. Toggle the server on in GitHub Copilot Chat and verify the tool list
> 4. Run two chat prompts that exercise schema discovery and query generation against `dbo.Products`
> 5. Replicate the configuration for Copilot in Microsoft Fabric with the HTTP+SSE transport
> 6. Confirm permission boundaries by trying to run an INSERT through the MCP tool

## Prerequisites

- **Lab 01** completed — the `Lab01_Products` database with 12 product rows
- **VS Code** with the **GitHub Copilot** and **GitHub Copilot Chat** extensions installed
- **Node.js 20+** on PATH (the MCP server is launched via `npx`)
- Either:
  - An **Entra ID account** with permission to register an app and assign it a SQL login (preferred), **or**
  - A **SQL authentication user** scoped to `Lab01_Products`
- For the Fabric portion: access to a **Microsoft Fabric workspace** with a lakehouse and a Copilot in Fabric trial enabled
- Familiarity with `Authentication=ActiveDirectoryManagedIdentity` / `Authentication=ActiveDirectoryInteractive` connection strings

---

## Setup

The setup is mostly database-side: create the read-only MCP user the AI
assistant will impersonate.

```sql
USE Lab01_Products;
GO

-- Option A — Entra ID user (preferred). Replace the principal name with your
-- service principal or user UPN.
CREATE USER [mcp-reader@contoso.com] FROM EXTERNAL PROVIDER;

-- Option B — SQL authentication user. Skip if you used Option A.
-- CREATE USER mcp_reader WITHOUT LOGIN;
-- ALTER LOGIN <login_name> ENABLE;  -- if you created a login for it

-- Grant the minimum needed for schema discovery + read queries
GRANT VIEW DEFINITION ON SCHEMA::dbo TO [mcp-reader@contoso.com];
GRANT SELECT          ON SCHEMA::dbo TO [mcp-reader@contoso.com];

-- Explicitly deny anything sensitive — DDM / RLS / cross-schema secrets.
-- This pattern stops Copilot from being prompted into reading the wrong table.
-- DENY SELECT ON dbo.Salaries TO [mcp-reader@contoso.com];  -- example only

-- Verify
SELECT class_desc, permission_name, state_desc,
       OBJECT_SCHEMA_NAME(major_id) AS SchemaName
FROM sys.database_permissions
WHERE grantee_principal_id = USER_ID(N'mcp-reader@contoso.com');
```

**Expected output**

| class_desc | permission_name  | state_desc | SchemaName |
| :--------- | :--------------- | :--------- | :--------- |
| SCHEMA     | VIEW DEFINITION  | GRANT      | dbo        |
| SCHEMA     | SELECT           | GRANT      | dbo        |

---

## Steps

### Step 1: Author `.vscode/mcp.json` for VS Code + GitHub Copilot

VS Code reads MCP server configuration from `.vscode/mcp.json` at the workspace
root. The block below launches `@modelcontextprotocol/server-mssql` over stdio
and authenticates with Entra ID's interactive flow on first use.

```json
{
  "servers": {
    "lab-products": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-mssql"],
      "env": {
        "MSSQL_CONNECTION_STRING": "Server=tcp:myserver.database.windows.net,1433;Database=Lab01_Products;Authentication=ActiveDirectoryInteractive;Encrypt=True;TrustServerCertificate=False;"
      }
    }
  }
}
```

For a Managed Identity in Azure (Functions, App Service, VM):

```json
{
  "servers": {
    "lab-products": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-mssql"],
      "env": {
        "MSSQL_CONNECTION_STRING": "Server=tcp:myserver.database.windows.net,1433;Database=Lab01_Products;Authentication=ActiveDirectoryManagedIdentity;Encrypt=True;"
      }
    }
  }
}
```

**Expected output** — open the Copilot Chat panel and the **Tools** wrench
icon now lists `lab-products`. Toggle it on. The server process starts on
demand and shuts down with the session.

**Why this matters** — the exam tests where MCP config lives in VS Code
(`.vscode/mcp.json`, `servers` key) vs Claude Desktop / Cursor (`mcpServers`
key). Same tools; different config root.

---

### Step 2: Verify the MCP tool list

In Copilot Chat, type `#lab-products` and observe the tool autocomplete. Or
ask the assistant directly:

```text
@workspace What tools does the lab-products MCP server expose? List each
tool's name and what it does.
```

**Expected output** — the assistant lists tools roughly like:

```text
- list_databases     — list databases on the connected server
- list_schemas       — list schemas in the connected database
- list_tables        — list tables in a schema, with column info on request
- describe_table     — return columns, types, indexes, constraints for a table
- execute_query      — run a read-only SQL query and return rows
```

The exact tool names depend on the `@modelcontextprotocol/server-mssql`
version. The structure (`name` + `description` + `inputSchema`) is the same
across versions.

**Why this matters** — the exam tests the difference between an MCP **tool**
(a callable action) and an MCP **resource** (a static piece of data the model
can read). MSSQL exposes both, with tools dominating.

---

### Step 3: Run a schema-aware prompt

Copilot now has live access to your schema. Try:

```text
Using lab-products, write a query that returns the average length of the
Description column grouped by Category, sorted descending.
```

**Expected output** — Copilot invokes `describe_table` on `dbo.Products`,
sees the `Category` and `Description` columns, and emits something like:

```sql
SELECT
    Category,
    AVG(LEN(Description)) AS AvgDescLen
FROM dbo.Products
GROUP BY Category
ORDER BY AvgDescLen DESC;
```

When the assistant has tool access, this is a noticeable upgrade over
schemaless chat: it cannot hallucinate column names because it reads them
first.

**Why this matters** — the exam tests this exact value proposition: MCP
gives Copilot **read access to schema**, which both improves SQL quality and
constrains queries to columns that actually exist.

---

### Step 4: Confirm the permission boundary

The MCP service account from Setup has `SELECT` + `VIEW DEFINITION` only. Ask
Copilot to perform a write:

```text
Using lab-products, write and execute an INSERT that adds a "Test Product"
row to dbo.Products.
```

**Expected output** — Copilot calls `execute_query` with the INSERT. The MCP
server returns a structured error roughly like:

```json
{
  "error": {
    "code": "PERMISSION_DENIED",
    "message": "INSERT permission was denied on the object 'Products', database 'Lab01_Products', schema 'dbo'.",
    "data": { "operation": "INSERT", "object": "dbo.Products" }
  }
}
```

Copilot surfaces the error inline. **Importantly**, the database stayed
read-only — even though the prompt asked for a write.

**Why this matters** — DP-800 hits this exact security question. MCP servers
inherit the connection-string user's permissions. The right defence is at the
SQL principal layer, not in clever prompt engineering.

---

### Step 5: Wire the same database to Copilot in Microsoft Fabric

Copilot in Microsoft Fabric reads MCP configuration from the Fabric workspace
settings (Admin portal → AI / Copilot → MCP endpoints). The transport is
**HTTP+SSE**, not stdio — Fabric runs the MCP server in the same control
plane as the workspace.

```json
{
  "servers": {
    "lab-products-fabric": {
      "type": "http",
      "url": "https://api.fabric.microsoft.com/v1/workspaces/{workspaceId}/mcp/sql/{databaseId}",
      "headers": {
        "Authorization": "Bearer ${env:FABRIC_TOKEN}"
      }
    }
  }
}
```

> [!note] Preview-only step
> The hosted Fabric MCP endpoint URL above follows the documented pattern but
> is **preview** in selected regions as of the March 2026 blueprint. If your
> tenant does not yet expose it, the rest of this lab still works end-to-end
> against the stdio MCP server from Steps 1–4 — the Fabric integration is the
> same model, just over HTTP+SSE instead of stdio.

Once registered, the Fabric Copilot side panel lets you address the database
with the same chat patterns as Step 3.

**Why this matters** — the exam contrasts stdio (local dev) vs HTTP+SSE
(hosted) transports. Fabric is the canonical example of the hosted side.

---

### Step 6: Inspect the request/response flow

The `npx`-launched server writes JSON-RPC over stdio. Tail the VS Code
**MCP servers** output panel (Command Palette → "MCP: Show Output") to see:

```text
> { "jsonrpc":"2.0","id":1,"method":"initialize", ... }
< { "jsonrpc":"2.0","id":1,"result": { "capabilities": { ... } } }
> { "jsonrpc":"2.0","id":2,"method":"tools/list" }
< { "jsonrpc":"2.0","id":2,"result": { "tools": [ ... ] } }
> { "jsonrpc":"2.0","id":3,"method":"tools/call",
    "params":{ "name":"execute_query","arguments":{ "query":"SELECT TOP 3 ProductId, ProductName FROM dbo.Products" } } }
< { "jsonrpc":"2.0","id":3,"result": { "content":[{ "type":"text","text":"[{...3 rows...}]" }] } }
```

**Expected output** — the panel shows the initialize handshake, the tools
manifest, and each `tools/call` followed by its structured response. Errors
appear as `result.isError = true` or as a top-level `error` object.

**Why this matters** — the exam asks "what protocol does MCP use?" The answer
is **JSON-RPC 2.0** over a transport (stdio or HTTP+SSE). Knowing what flows
on the wire makes the abstract protocol concrete.

---

## Cleanup

```sql
USE Lab01_Products;
GO

DROP USER IF EXISTS [mcp-reader@contoso.com];
-- DROP USER IF EXISTS mcp_reader;  -- if you used Option B

-- The lab's .vscode/mcp.json lives in your workspace, not in the database.
-- Delete the file or remove the "lab-products" entry from your config.
```

Stop the stdio MCP server by closing VS Code, or open the **Tools** panel in
Copilot Chat and toggle `lab-products` off.

---

## Common Issues & Errors

| Error / symptom | Cause | Fix |
| :--- | :--- | :--- |
| `Login failed for user '<token-identified principal>'` when MCP starts | The Entra ID user does not exist as a database user, or lacks `CONNECT` | Re-run `CREATE USER ... FROM EXTERNAL PROVIDER;` and `GRANT CONNECT ON DATABASE` |
| `npx` cannot find `@modelcontextprotocol/server-mssql` | Stale npx cache or package name typo | `npx clear-npx-cache`, retry. The package may also be named `@modelcontextprotocol/server-mssql` or `@microsoft/mcp-server-sql` depending on the version pinned in your tenant |
| MCP tool shows up but `tools/list` is empty | Server started but cannot reach the database (firewall / VNet) | Confirm with `sqlcmd` from the same machine; whitelist the client IP on the Azure SQL firewall |
| Copilot ignores the tool and writes hallucinated SQL | The MCP server entry is registered but the tool toggle is off in the session | Open the **Tools** panel (wrench icon), confirm `lab-products` is enabled |
| Fabric MCP endpoint returns `401` after a few minutes | Fabric bearer tokens are short-lived | Refresh `${env:FABRIC_TOKEN}`; use a service principal credential if you need long-lived access |

---

## Exam Tips

> [!tip] Exam Tips
>
> - MCP configuration goes in `.vscode/mcp.json` (VS Code) or `mcpServers` (Claude Desktop / Cursor). Tools manifest is identical across config formats
> - Prefer **Managed Identity** (`Authentication=ActiveDirectoryManagedIdentity`) over SQL authentication — the exam hits this every form
> - MCP servers run with the **permissions of the connection-string user** — defence-in-depth lives at the SQL principal layer, not in the prompt
> - **stdio** transport is for local servers; **HTTP+SSE** is for hosted endpoints like Fabric's lakehouse MCP. Same protocol (JSON-RPC 2.0), different transport

---

## Key Takeaways

- MCP is an open protocol (JSON-RPC 2.0 over stdio or HTTP+SSE) — not a Microsoft service
- VS Code reads `.vscode/mcp.json`; the `servers` block declares each MCP endpoint
- Least-privilege SQL principal + Managed Identity is the standard security posture for MCP
- Tool errors are surfaced inline in the chat — they do not silently succeed, but they also do not stop the conversation

---

## Related Topics

- [03-MCP Server Endpoints](../../04-ai-assisted-tools/03-mcp-server-endpoints.md)
- [02-GitHub Copilot Setup](../../04-ai-assisted-tools/02-github-copilot-setup.md)
- [03-Permissions & Access](../../05-data-security-compliance/03-permissions-access.md)
- [01-AI Security Impact](../../04-ai-assisted-tools/01-ai-security-impact.md)

---

## Official Documentation

- <https://modelcontextprotocol.io/>
- <https://learn.microsoft.com/en-us/sql/tools/mcp/overview>
- <https://learn.microsoft.com/en-us/fabric/fundamentals/copilot-fabric-overview>
- <https://learn.microsoft.com/en-us/azure/azure-sql/database/authentication-aad-overview>
- <https://learn.microsoft.com/en-us/entra/identity/managed-identities-azure-resources/overview>

---

**[← Back to lab index](./labs.md) | [↑ Back to overview](../../dp-800-overview.md)**
