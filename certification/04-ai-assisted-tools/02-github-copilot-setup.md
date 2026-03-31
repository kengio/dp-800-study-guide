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

> [!abstract]
> - Covers GitHub Copilot features for database development: inline suggestions, Copilot Chat, slash commands
> - Copilot suggests; it does not execute — all suggestions require human review
> - Key exam topics: Copilot Chat slash commands (/explain, /fix, /doc), inline completion behavior, Azure SQL setup

> [!tip] What the Exam Tests
> - Copilot provides **suggestions only** — it cannot run SQL or make changes without explicit developer action
> - Slash commands: `/explain` = explain selected code; `/fix` = suggest a fix; `/doc` = generate documentation; `/tests` = generate tests
> - Copilot for Azure SQL in SSMS/VS Code requires the GitHub Copilot extension + appropriate license

---

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

---

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

---

## Copilot Instruction Files

**Copilot instruction files** provide repository-specific context that Copilot includes automatically in every chat session.

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

---

## Configuring Model Options in Chat

### Selecting the Model

In a GitHub Copilot Chat session, you can choose the AI model:

```text
Copilot Chat > Model picker (top of chat panel)
```

Available models (as of early 2026, varies by subscription):

| Model | Strengths for SQL/Database Work |
|:---|:---|
| GPT-4o | General-purpose SQL generation, fast responses |
| o3-mini | ==Reasoning-heavy tasks, complex query logic== |
| Claude 3.5 Sonnet | Long-context schema understanding, code review |
| Claude 3.7 Sonnet | Extended reasoning, complex multi-step analysis |
| Gemini 2.0 Flash | Fast completions, broad multi-modal context |

For SQL development tasks:

- **GPT-4o**: Good general-purpose SQL generation
- **Claude models**: Strong for long-context reasoning and complex schema understanding
- **o3-mini**: Best for multi-step query logic and debugging

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

---

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

---

## Copilot for Azure SQL and Fabric SQL

### Copilot in the Azure Portal for Azure SQL Database

The Azure portal embeds Copilot directly in the Query Editor for Azure SQL Database:

- **Natural language to SQL**: Type a description and Copilot generates the T-SQL
- **Explain query**: Highlight a query and ask Copilot to explain what it does
- **Fix suggestions**: Copilot surfaces fixes when a query returns errors
- **No extension required**: Available natively in the portal Query Editor

Access path:

```text
Azure Portal → Azure SQL Database → Query editor (preview)
→ Copilot button or inline suggestions
```

### Copilot in Microsoft Fabric for SQL

Fabric provides Copilot for both **SQL analytics endpoints** (Lakehouse) and **Fabric SQL databases**:

| Surface | Copilot Capability |
|:---|:---|
| SQL analytics endpoint | Natural language to T-SQL, explain errors |
| Fabric SQL database | ==Generate, explain, fix T-SQL; schema-aware== |
| Notebook (Spark SQL) | SQL cell generation, explain output |

**Key Fabric SQL Copilot features:**

- Generate T-SQL from natural language descriptions of the desired result
- Explain error messages and suggest corrective T-SQL
- Suggest query rewrites for performance
- Schema-aware: Copilot reads your Fabric SQL database schema in context

### Integration with Azure AI Foundry

Fabric Copilot can be enhanced with models deployed in Azure AI Foundry:

- Connect a Fabric workspace to an Azure AI Foundry project
- Use custom or fine-tuned models for domain-specific SQL generation
- Enables richer context when working with proprietary data schemas

---

## Custom Instructions Deep-Dive

### The `.github/copilot-instructions.md` File

This file is loaded automatically into every Copilot Chat session for users in that repository. It is the primary mechanism for persistent, repo-level Copilot customization.

- Stored at the **repository root** under `.github/`
- Plain Markdown; no special syntax required
- All team members sharing the repo get the same instructions
- Loaded in addition to any user-level or session instructions

### VS Code Settings for Code Generation Instructions

For user-level or workspace-level instructions, configure in VS Code settings:

```json
// .vscode/settings.json (workspace) or settings.json (user)
{
    "github.copilot.chat.codeGeneration.instructions": [
        {
            "text": "Always use schema prefixes (dbo.TableName). Use THROW not RAISERROR."
        }
    ]
}
```

This complements (not replaces) the repo-level instructions file.

### Prompt Engineering Best Practices for SQL Contexts

When writing instructions for a SQL/database project, always specify:

1. **Target platform** — Azure SQL Database, Fabric SQL, SQL Server 2022, etc.
2. **Compatibility level** — e.g., `ALTER DATABASE SET COMPATIBILITY_LEVEL = 160`
3. **Forbidden syntax** — cursors, deprecated types, `SELECT *`, `RAISERROR`
4. **Naming conventions** — schema prefixes, casing (PascalCase vs snake_case)
5. **Error handling pattern** — `TRY/CATCH` + `THROW` vs legacy patterns

### Example `copilot-instructions.md` for SQL Projects

```markdown
## SQL Development Guidelines

- Target platform: Azure SQL Database (latest compatibility level)
- Always use schema prefixes: `dbo.TableName`
- Prefer CTEs over nested subqueries
- Use `NVARCHAR` for all string columns
- Always include `SET NOCOUNT ON` in stored procedures
- Use `THROW` not `RAISERROR` for error handling
- Avoid cursors; prefer set-based operations
```

---

## Copilot CLI for Database Projects

### Using `gh copilot suggest` from the Terminal

The GitHub CLI Copilot extension allows natural language SQL generation outside of an IDE:

```bash
# Install the gh copilot extension
gh extension install github/gh-copilot

# Ask for a T-SQL snippet
gh copilot suggest "write a T-SQL query to find customers with no orders in 90 days"

# Explain a command or script
gh copilot explain "sp_WhoIsActive"
```

Useful for quick generation tasks in CI/CD scripts or when not in VS Code.

### GitHub Copilot Extensions for Database Tools

Copilot Extensions (GitHub Marketplace) allow third-party database tools to integrate:

- Extensions can surface schema metadata, query history, or ERD context into Copilot Chat
- Use `@extension-name` in Copilot Chat to invoke a registered extension
- Enterprise plans support private Copilot Extensions for internal tooling

### Integration with SQL Database Projects (`sqlproj`)

When a repository contains a `.sqlproj` file, Copilot becomes schema-aware:

- Reads DACPAC/schema objects defined in the project
- Generates T-SQL consistent with the declared schema
- Inline completions suggest table and column names from the project schema
- Works with the **SQL Database Projects** extension in VS Code

---

## Evaluating AI-Generated SQL

AI-generated SQL should always be reviewed before execution in production.

### Pre-Production Checklist

- [ ] **SQL injection risk**: Dynamic SQL built with user input must use `sp_executesql` with parameters
- [ ] **Column names**: Verify against actual schema — Copilot may hallucinate column names
- [ ] **Implicit conversions**: Check for mismatched types (`NVARCHAR` vs `VARCHAR`, `DATETIME` vs `DATETIME2`)
- [ ] **Join correctness**: Confirm joins are on the intended keys, especially for multi-table queries
- [ ] **Index usage**: Run with `SET STATISTICS IO ON` to verify seeks vs scans

### Safe vs Unsafe Dynamic SQL Pattern

```sql
-- UNSAFE: direct string concatenation (SQL injection risk)
DECLARE @sql NVARCHAR(500) = 'SELECT * FROM dbo.Users WHERE Name = ''' + @UserInput + '''';
EXEC (@sql);

-- SAFE: parameterized with sp_executesql
DECLARE @sql NVARCHAR(500) = N'SELECT * FROM dbo.Users WHERE Name = @Name';
EXEC sp_executesql @sql, N'@Name NVARCHAR(100)', @Name = @UserInput;
```

AI models often generate the unsafe pattern. Always replace direct concatenation with `sp_executesql` when user input is involved.

---

## Use Cases

- **Query generation**: Describe what you need in English, get T-SQL
- **Schema exploration**: Ask Copilot to explain a table or procedure (with MCP connected)
- **Code review**: Ask Copilot to check for SQL injection or performance issues
- **Documentation**: Generate inline comments and procedure documentation
- **Azure portal**: Use embedded Copilot in Azure SQL Query Editor for ad-hoc work

---

## Common Issues & Errors

| Issue | Cause | Resolution |
|:---|:---|:---|
| Copilot not suggesting SQL | Extension not installed | Install GitHub Copilot + Copilot Chat extensions |
| Instructions file not used | Wrong location or format | ==Must be `.github/copilot-instructions.md` at repo root== |
| MCP server not connecting | Configuration error | Check `mcp.json` and environment variables |
| Hallucinated column names | Model lacks schema context | Add schema summary to instructions file or use MCP |
| Wrong model available | Subscription tier | Enterprise plans unlock all models; Individual has subset |

---

## Best Practices

- Always add a `.github/copilot-instructions.md` with target platform, naming conventions, and forbidden patterns — this is the most impactful Copilot customization for a SQL project.
- Review all AI-generated dynamic SQL for injection risks before execution; prefer `sp_executesql` with parameters.
- Use the model picker deliberately — Claude 3.7 Sonnet for complex reasoning tasks, GPT-4o or Gemini 2.0 Flash for fast completions.
- Combine MCP server configuration with instruction files to give Copilot both live schema access and coding standards.
- Treat Copilot output as a first draft: always validate column names and join logic against the actual schema.

---

## Exam Tips

> [!tip] Exam Tips
> - **Instruction files** are at `.github/copilot-instructions.md` — know the exact location
> - Model selection is available in Copilot Chat — not the inline completion
> - MCP tool configuration can be scoped: session-level vs persistent (`.vscode/mcp.json`)
> - Copilot in Fabric is enabled at the **tenant level** by a Fabric admin
> - The Azure portal has its own embedded Copilot for Azure SQL — separate from GitHub Copilot
> - VS Code `github.copilot.chat.codeGeneration.instructions` is user/workspace level; `.github/copilot-instructions.md` is repo level

---

## Practice Question

A developer wants GitHub Copilot to always generate T-SQL for Azure SQL Database with schema prefixes and THROW for error handling. Which approach persists these instructions across all Copilot sessions in the repository?

A. Set instructions in each individual VS Code chat session
B. Create a `.github/copilot-instructions.md` file in the repository root
C. Configure system prompt in the GitHub Copilot extension settings.json
D. Add instructions as code comments in each SQL file

> [!success]- Answer
> **B — Create a `.github/copilot-instructions.md` file in the repository root**
>
> The `.github/copilot-instructions.md` file is automatically loaded by GitHub Copilot for all chat interactions in that repository. It persists across sessions and team members. Per-session instructions (A) don't persist. Extension settings (C) are user-level, not repo-level. Code comments (D) provide context for the current file only.

---

## Key Takeaways

- Instruction files provide project-specific context to every Copilot chat session
- Model and MCP tool options are configured per-session or persistently in config files
- Copilot in Fabric is separate from GitHub Copilot but uses the same underlying models
- Azure SQL Database has native Copilot in the Azure portal Query Editor
- Always validate AI-generated SQL for injection risks, schema accuracy, and implicit type conversions

---

## Related Topics

- [01-AI Security Impact](./01-ai-security-impact.md)
- [03-MCP Server Endpoints](./03-mcp-server-endpoints.md)

---

## Official Documentation

- [GitHub Copilot Docs](https://docs.github.com/en/copilot)
- [Copilot Custom Instructions](https://docs.github.com/en/copilot/customizing-copilot/adding-repository-custom-instructions-for-github-copilot)
- [Copilot in Fabric](https://learn.microsoft.com/en-us/fabric/fundamentals/copilot-fabric-overview)
- [Copilot in Azure SQL Database](https://learn.microsoft.com/en-us/azure/azure-sql/copilot/copilot-azure-sql-overview)
- [GitHub Copilot Extensions](https://docs.github.com/en/copilot/using-github-copilot/using-extensions-to-integrate-external-tools-with-copilot-chat)

---

**[← Previous](./01-ai-security-impact.md) | [↑ Back to Section](./ai-assisted-tools.md) | [Next →](./03-mcp-server-endpoints.md)**
