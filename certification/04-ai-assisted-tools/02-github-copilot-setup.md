---
title: GitHub Copilot and Copilot in Fabric Setup
type: study-material
tags:
  - dp-800
  - github-copilot
  - copilot-in-fabric
  - instruction-files
  - model-options
---

# GitHub Copilot and Copilot in Fabric Setup

## Overview

The DP-800 exam covers enabling GitHub Copilot and Copilot in Fabric, configuring model and Model Context Protocol (MCP) tool options, and creating Copilot instruction files to provide project-specific context.

## Enabling GitHub Copilot

### For Individual Developers

1. Subscribe to GitHub Copilot (Individual, Business, or Enterprise)
2. Install the GitHub Copilot extension in your IDE (VS Code, Visual Studio, Azure Data Studio)
3. Sign in with your GitHub account

### For Organizations

```yaml
# Organization Settings > Copilot
# - Enable/disable features
# - Set content exclusion policies
# - Configure network proxy
# - Review usage and audit logs
```

### In Azure Data Studio / VS Code for SQL

1. Install the **GitHub Copilot** extension
2. Install the **GitHub Copilot Chat** extension
3. Use **Copilot Chat** panel for SQL generation: `Ctrl+Shift+I`
4. Use inline completions while writing T-SQL

## Enabling Copilot in Microsoft Fabric

Copilot in Fabric is the integrated AI assistant for Fabric workloads (SQL databases, notebooks, pipelines).

```text
Fabric Portal → Settings → Admin portal → Tenant settings
→ Copilot and Azure OpenAI Service → Enable
```

**Copilot in Fabric SQL database:**
- Generates T-SQL from natural language
- Explains query execution plans
- Suggests query optimizations
- Available in the SQL query editor

## Copilot Instruction Files

Copilot instruction files provide repository-specific context that Copilot includes automatically in every chat session.

### Creating a GitHub Copilot Instructions File

```markdown
<!-- .github/copilot-instructions.md -->

## Project Context
This is a SQL database project for an e-commerce platform.
Database: Azure SQL Database (SQL Server 2022 compatibility)

## Conventions
- Use two-part names (dbo.TableName) for all objects
- Always include SET NOCOUNT ON in stored procedures
- Use datetime2(0) instead of datetime for all date columns
- Prefer inline TVFs over scalar functions for set-based operations
- Use THROW for error handling (not RAISERROR)
- All stored procedures must use TRY/CATCH with transaction management

## Schema Summary
- dbo.Customers (CustomerId, Name, Email, IsActive)
- dbo.Orders (OrderId, CustomerId, OrderDate, TotalAmount)
- dbo.OrderItems (OrderId, ProductId, Quantity, UnitPrice)
- dbo.Products (ProductId, Name, Price, CategoryId, Attributes JSON)

## Do Not
- Use SELECT * in production queries
- Hardcode connection strings or credentials
- Use deprecated data types (datetime, text, image)
```

**File location:** `.github/copilot-instructions.md` (GitHub Copilot reads this automatically)

## Configuring Model Options in Chat

### Selecting the Model

In a GitHub Copilot Chat session, you can choose the AI model:

```text
Copilot Chat > Model picker (top of chat panel)
Options: GPT-4o, Claude 3.5 Sonnet, o1, Gemini 1.5 Pro (varies by subscription)
```

For SQL development tasks:
- **GPT-4o**: Good general-purpose SQL generation
- **Claude models**: Strong for long-context reasoning and complex schema understanding

### Configuring MCP Tool Options

Model Context Protocol tools extend what Copilot can access in a chat session:

```json
// .vscode/mcp.json (VS Code MCP configuration)
{
    "servers": {
        "sql-server": {
            "type": "stdio",
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-mssql"],
            "env": {
                "MSSQL_CONNECTION_STRING": "${env:MSSQL_CONNECTION_STRING}"
            }
        }
    }
}
```

In a chat session, enable/disable available tools with the **Tools** toggle or `#tool` references.

## Using Copilot for SQL Development

### Generating Queries from Natural Language

```text
@workspace /explain this stored procedure

Write a stored procedure to transfer funds between accounts with proper
error handling and transaction management
```

### Explaining Execution Plans

```text
Explain this execution plan and suggest improvements:
[paste plan XML or describe operators]
```

### Code Review

```text
Review this T-SQL for security vulnerabilities and performance issues:
[paste T-SQL code]
```

## Use Cases

- **Query generation**: Describe what you need in English, get T-SQL
- **Schema exploration**: Ask Copilot to explain a table or procedure (with MCP connected)
- **Code review**: Ask Copilot to check for SQL injection or performance issues
- **Documentation**: Generate inline comments and procedure documentation

## Common Issues & Errors

| Issue | Cause | Resolution |
|:---|:---|:---|
| Copilot not suggesting SQL | Extension not installed | Install GitHub Copilot + Copilot Chat extensions |
| Instructions file not used | Wrong location or format | Must be `.github/copilot-instructions.md` at repo root |
| MCP server not connecting | Configuration error | Check `mcp.json` and environment variables |

## Exam Tips

- **Instruction files** are at `.github/copilot-instructions.md` — know the location
- Model selection is available in Copilot Chat — not the inline completion
- MCP tool configuration can be scoped: session-level vs persistent (`.vscode/mcp.json`)
- Copilot in Fabric is enabled at the **tenant level** by a Fabric admin

## Key Takeaways

- Instruction files provide project-specific context to every Copilot chat session
- Model and MCP tool options are configured per-session or persistently in config files
- Copilot in Fabric is separate from GitHub Copilot but uses the same underlying models

## Related Topics

- [01-AI Security Impact](./01-ai-security-impact.md)
- [03-MCP Server Endpoints](./03-mcp-server-endpoints.md)

## Official Documentation

- [GitHub Copilot Docs](https://docs.github.com/en/copilot)
- [Copilot Custom Instructions](https://docs.github.com/en/copilot/customizing-copilot/adding-repository-custom-instructions-for-github-copilot)
- [Copilot in Fabric](https://learn.microsoft.com/en-us/fabric/fundamentals/copilot-fabric-overview)

---

**[← Previous](./01-ai-security-impact.md) | [↑ Back to Section](./README.md) | [Next →](./03-mcp-server-endpoints.md)**
