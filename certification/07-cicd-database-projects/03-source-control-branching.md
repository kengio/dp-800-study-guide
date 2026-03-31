---
title: Source Control and Branching for Database Projects
type: study-material
tags:
  - dp-800
  - git
  - branching
  - pull-requests
---

# Source Control and Branching for Database Projects

## Overview

Storing SQL Database Projects in Git enables collaboration, history tracking, and structured review of schema changes. Branching strategies control how schema changes move from development to production, while branch policies and pull requests enforce quality gates before changes are merged.

> [!abstract]
> - Covers Git-based source control for database schema files, branching strategies, and merge conflict resolution
> - Database schema files (.sql) in a project are treated the same as application code — same Git workflows apply
> - Key exam topics: feature branch workflow, PR-based review, handling schema file merge conflicts

> [!tip] What the Exam Tests
> - Database schema changes go through the same feature branch → PR → merge → deploy workflow as application code
> - Merge conflicts in schema `.sql` files must be resolved manually — Git cannot auto-resolve SQL syntax conflicts
> - The `.sqlproj` file itself can have conflicts if two branches add different objects

---

## Configuring Source Control for SQL Database Projects

### Repository Structure

```text
repo-root/
├── src/
│   └── MyDatabase/
│       ├── MyDatabase.sqlproj
│       ├── Schema/
│       │   ├── Tables/
│       │   ├── Views/
│       │   └── StoredProcedures/
│       └── Scripts/
│           ├── PreDeployment/
│           └── PostDeployment/
├── tests/
│   └── MyDatabase.Tests/
│       └── ... (tSQLt test files or separate test project)
├── pipelines/
│   ├── build.yml
│   └── deploy.yml
├── .gitignore
└── README.md
```

### .gitignore for SQL Projects

```gitignore
# Build output
bin/
obj/

# Visual Studio
.vs/
*.user
*.suo

# SQL Server Object Explorer
*.publish.xml

# Local connection settings (never commit connection strings)
*.pubxml
localSettings.json
```

### Connecting VS Code / Azure Data Studio to Git

```bash
# Initialize new repo
git init
git remote add origin https://dev.azure.com/myorg/myproject/_git/my-database

# Clone existing
git clone https://dev.azure.com/myorg/myproject/_git/my-database
```

SQL Database Projects extension in VS Code / Azure Data Studio provides:
- Schema compare between database and project
- One-click "Update Project from Database" to capture current state
- Integrated Git panel for staging and committing schema changes

---

## Branching Strategies

### Git Flow (Standard for Database Projects)

```text
main          ●────────────────────────────────────────●──→ (production)
               \                                      /
release/1.2     ●──────────────────────────────────●
                 \                                /
feature/add-idx   ●──────────────────────────●
                                                \
hotfix/fix-sproc                               ●──→ (cherry-pick to main)
```

**Branch roles:**

| Branch | Purpose | Deploys To |
| :--- | :--- | :--- |
| `main` | ==Production-ready code== | Production |
| `release/x.y` | Release stabilization | Staging/UAT |
| `feature/*` | New tables, columns, procedures | Dev environment |
| `hotfix/*` | Emergency production fixes | Production (via main) |

### Trunk-Based Development (Simpler Alternative)

```text
main      ●─────●─────●─────●─────●──→ (continuous deployment to dev)
           \   /  \  /  \  /  \  /
feat/A      ●      ●    ●    ●         (short-lived feature branches)
```

- Short-lived feature branches (1–3 days)
- Merged to `main` via pull request
- Main is always deployable
- Feature flags control exposure of incomplete features

---

## Pull Requests for Schema Changes

Pull requests enforce review before merging schema changes. For database projects, the PR diff shows the actual T-SQL changes.

### Branch Policy Configuration (Azure DevOps)

```yaml
# Branch policies for 'main' branch (configured in Azure DevOps portal)
# These are enforced automatically:
# - Require minimum 2 reviewers
# - Require successful build (CI pipeline must pass)
# - Require linked work items
# - Restrict who can push directly to main
# - Automatically include code owners as reviewers
```

### CODEOWNERS File

**CODEOWNERS** files automatically add reviewers based on file paths — making them essential for database change governance.

```text
# .github/CODEOWNERS or Azure DevOps equivalent
# Automatically add reviewers based on changed files

# All SQL files require a DBA review
*.sql @dba-team

# Security schema requires security team approval
/src/MyDatabase/Schema/Security/ @security-team

# Pre/post deployment scripts require senior DBA
/src/MyDatabase/Scripts/ @senior-dba-team
```

### What to Review in a Database PR

```sql
-- Example: PR adds a NOT NULL column without a default
-- This is a breaking change — reviewer should catch it

-- BAD: will fail on non-empty table
ALTER TABLE dbo.Orders ADD AuditUser NVARCHAR(50) NOT NULL;

-- GOOD: add with default, then optionally drop default later
ALTER TABLE dbo.Orders ADD AuditUser NVARCHAR(50) NOT NULL
    CONSTRAINT DF_Orders_AuditUser DEFAULT 'system';
```

**Schema change review checklist:**
- Are new NOT NULL columns backward compatible? (have defaults)
- Do column type changes risk data truncation?
- Are new indexes created `WITH (ONLINE = ON)` for live tables?
- Do stored procedure changes affect existing callers?
- Are pre-deployment scripts needed to migrate data?

---

## Conflict Resolution in Schema Files

Schema conflicts occur when two branches modify the same SQL object.

### Merge Conflict in a Table File

```sql
<<<<<<< HEAD
-- main branch version
CREATE TABLE [dbo].[Orders]
(
    [OrderId]    INT NOT NULL IDENTITY(1,1),
    [CustomerId] INT NOT NULL,
    [Status]     NVARCHAR(20) NOT NULL DEFAULT 'Pending',
    CONSTRAINT [PK_Orders] PRIMARY KEY ([OrderId])
);
=======
-- feature branch version
CREATE TABLE [dbo].[Orders]
(
    [OrderId]    INT NOT NULL IDENTITY(1,1),
    [CustomerId] INT NOT NULL,
    [Status]     NVARCHAR(20) NOT NULL DEFAULT 'Pending',
    [Priority]   INT NOT NULL DEFAULT 0,              -- new column
    CONSTRAINT [PK_Orders] PRIMARY KEY ([OrderId])
);
>>>>>>> feature/add-priority
```

**Resolution:**

```sql
-- Resolved: include both changes
CREATE TABLE [dbo].[Orders]
(
    [OrderId]    INT NOT NULL IDENTITY(1,1),
    [CustomerId] INT NOT NULL,
    [Status]     NVARCHAR(20) NOT NULL DEFAULT 'Pending',
    [Priority]   INT NOT NULL DEFAULT 0,
    CONSTRAINT [PK_Orders] PRIMARY KEY ([OrderId])
);
```

### Tips for Minimizing Schema Conflicts

- **One object per file**: Conflicts are isolated to single-object files
- **Avoid large omnibus changes**: Small, focused PRs are easier to merge
- **Keep feature branches short-lived**: Reduces divergence from `main`
- **Use Schema Compare before merging**: Validate the merged result against a real database

---

## Use Cases

- **Feature branch workflow**: Developers create `feature/add-order-priority` branch, make schema changes, open PR for DBA review before merging
- **Release branch**: Lock down the schema for a release, apply only bugfixes — no new feature schema
- **CODEOWNERS for DBA enforcement**: Any change to `Schema/` automatically requests DBA team review
- **Hotfix branch**: Emergency fix to a stored procedure — branch from `main`, fix, PR, merge, deploy immediately

---

## Common Issues & Errors

| Issue | Cause | Fix |
| :--- | :--- | :--- |
| Merge conflict in `.sqlproj` | Both branches added files | Open `.sqlproj`, keep all `<Build>` entries (SDK-style usually auto-includes, so conflict may not occur) |
| PR build fails with unresolved reference | Object referenced in one branch, deleted in another | Resolve the merge conflict to include both the object definition and its reference |
| Direct push to `main` bypasses review | No branch protection | ==Enable branch protection rules in Azure DevOps or GitHub== |
| Schema Compare shows unexpected changes after merge | Merge introduced formatting differences | Use SSDT Schema Compare to validate actual structural differences |

---

## Exam Tips

> [!tip] Exam Tips
> - Branch policies in Azure DevOps (require reviewers, require build success) enforce quality gates — know how to configure them
> - CODEOWNERS files automatically add reviewers based on file paths — critical for database change governance
> - `main` branch should always reflect production-deployable state — use feature/release branches for in-progress work
> - Schema conflicts are best avoided by one-object-per-file conventions and short-lived branches
> - Pull request builds should run `dotnet build` to validate the dacpac compiles before allowing merge

---

## Key Takeaways

- SQL Database Projects belong in Git like any other code — one SQL object per file is best practice
- Branch policies (required reviewers, required builds) are the governance mechanism for database changes
- CODEOWNERS ensures domain experts (DBAs) automatically review changes to critical schema files
- Conflict resolution in schema files is straightforward when each object lives in its own file

---

## Related Topics

- [02-SQL Database Projects](./02-sql-database-projects.md)
- [04-Deployment Pipelines](./04-deployment-pipelines.md)
- [01-Testing Strategy](./01-testing-strategy.md)

---

## Official Documentation

- [SQL Projects Source Control](https://learn.microsoft.com/en-us/azure/azure-sql/database/sql-projects-overview)
- [Azure DevOps Branch Policies](https://learn.microsoft.com/en-us/azure/devops/repos/git/branch-policies)
- [GitHub CODEOWNERS](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners)

---

**[← Previous](./02-sql-database-projects.md) | [↑ Back to Section](./cicd-database-projects.md) | [Next →](./04-deployment-pipelines.md)**
