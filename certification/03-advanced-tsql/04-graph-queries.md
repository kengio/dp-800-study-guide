---
title: Graph Queries
type: study-material
tags:
  - dp-800
  - graph
  - match
  - node
  - edge
---

# Graph Queries

## Overview

SQL Server graph tables store node and edge data using special columns (`$node_id`, `$from_id`, `$to_id`) and support graph traversal with the `MATCH` predicate — enabling relationship queries without recursive CTEs.

> [!abstract]
> - Covers graph database objects (NODE tables, EDGE tables) and graph query syntax (MATCH, SHORTEST_PATH)
> - SQL graph tables are regular SQL tables with special system-generated columns for graph traversal
> - Key exam topics: NODE vs EDGE table creation, MATCH clause syntax, when graph outperforms relational (hierarchies)

> [!tip] What the Exam Tests
> - `CREATE TABLE … AS NODE` and `CREATE TABLE … AS EDGE` — EDGE tables reference NODE tables
> - `MATCH (Person)-[Knows]->(Person)` syntax is required for graph traversal — you cannot use regular JOINs for graph patterns
> - `SHORTEST_PATH` inside a `MATCH` clause finds the shortest path between two nodes in a connected graph

---

## Graph Table Types

```sql
-- Node table: represents entities
CREATE TABLE dbo.Person (
    PersonId    int             NOT NULL PRIMARY KEY,
    Name        nvarchar(100)   NOT NULL,
    City        nvarchar(100)   NULL
) AS NODE;

CREATE TABLE dbo.Restaurant (
    RestaurantId    int             NOT NULL PRIMARY KEY,
    Name            nvarchar(200)   NOT NULL,
    Cuisine         nvarchar(50)    NULL
) AS NODE;

-- Edge table: represents relationships
CREATE TABLE dbo.likes    AS EDGE;
CREATE TABLE dbo.friendOf AS EDGE;

-- Edge table with properties
CREATE TABLE dbo.Visited (
    VisitDate   date NOT NULL,
    Rating      int  NULL
) AS EDGE;
```

**System columns:**
- Node tables: `$node_id` (unique node identifier, JSON format internally)
- Edge tables: `$edge_id`, `$from_id` (source node), `$to_id` (target node)

---

## Inserting Graph Data

```sql
-- Insert nodes
INSERT INTO dbo.Person (PersonId, Name) VALUES (1, 'Alice'), (2, 'Bob'), (3, 'Carol');
INSERT INTO dbo.Restaurant (RestaurantId, Name, Cuisine)
VALUES (1, 'Sushi Palace', 'Japanese'), (2, 'Pizza Corner', 'Italian');

-- Insert edges using $node_id references
INSERT INTO dbo.likes ($from_id, $to_id)
VALUES (
    (SELECT $node_id FROM dbo.Person WHERE PersonId = 1),
    (SELECT $node_id FROM dbo.Restaurant WHERE RestaurantId = 1)
);

INSERT INTO dbo.friendOf ($from_id, $to_id)
VALUES (
    (SELECT $node_id FROM dbo.Person WHERE PersonId = 1),
    (SELECT $node_id FROM dbo.Person WHERE PersonId = 2)
);

-- Edge with properties
INSERT INTO dbo.Visited ($from_id, $to_id, VisitDate, Rating)
VALUES (
    (SELECT $node_id FROM dbo.Person WHERE PersonId = 2),
    (SELECT $node_id FROM dbo.Restaurant WHERE RestaurantId = 2),
    '2025-06-01', 5
);
```

---

## MATCH Predicate

The `MATCH` clause uses arrow notation for traversal:

```sql
-- Pattern syntax:
-- node-(edge)->node   : directed traversal (from → to)
-- node<-(edge)-node   : reverse traversal

-- Find all restaurants Alice likes
SELECT r.Name AS Restaurant
FROM dbo.Person p, dbo.likes l, dbo.Restaurant r
WHERE MATCH(p-(l)->r)
  AND p.Name = 'Alice';

-- Find friends of Alice
SELECT p2.Name AS Friend
FROM dbo.Person p1, dbo.friendOf f, dbo.Person p2
WHERE MATCH(p1-(f)->p2)
  AND p1.Name = 'Alice';

-- Chain: friends of Alice who like Japanese restaurants
SELECT p2.Name AS Friend, r.Name AS Restaurant
FROM dbo.Person p1, dbo.friendOf f, dbo.Person p2,
     dbo.likes l, dbo.Restaurant r
WHERE MATCH(p1-(f)->p2-(l)->r)
  AND p1.Name = 'Alice'
  AND r.Cuisine = 'Japanese';
```

> [!warning] Common Mistake
> Graph tables are still regular SQL tables — they support regular JOINs, indexes, and constraints. The MATCH clause is an additional query capability, not a replacement for all SQL. Don't confuse "graph table" with "NoSQL graph database."

---

## SHORTEST_PATH

`SHORTEST_PATH` finds the minimum-hop path between nodes using a recursive graph traversal pattern. The `FOR PATH` keyword is required on edge and intermediate node aliases inside the pattern.

Key functions used with `SHORTEST_PATH`:

- `LAST_NODE()` — returns the last node reached in the traversal path
- `STRING_AGG(...) WITHIN GROUP (GRAPH PATH)` — concatenates node values along the path in traversal order
- `COUNT(...) WITHIN GROUP (GRAPH PATH)` — counts hops or nodes along the path
- Quantifier `+` means one or more hops; `{1,N}` bounds the depth

```sql
-- Find shortest path from person to any connection (social network)
SELECT
    Person1.Name AS Source,
    LAST_NODE(Person2).Name AS Destination,
    COUNT(FriendOf.$edge_id) AS HopsCount,
    STRING_AGG(Person2.Name, '->') WITHIN GROUP (GRAPH PATH) AS Path
FROM
    Person AS Person1,
    friendOf FOR PATH AS FriendOf,
    Person FOR PATH AS Person2
WHERE
    MATCH(SHORTEST_PATH(Person1(-(FriendOf)->Person2)+))
    AND Person1.Name = 'Alice';
```

---

## Edge Constraints

Edge constraints enforce which node types are permitted on each side of an edge, preventing invalid connections at the schema level.

- Defined with `CONSTRAINT ... CONNECTION (NodeType TO NodeType)`
- Multiple connection pairs can be listed on a single edge table
- `ON DELETE CASCADE` removes edge rows automatically when a referenced node is deleted

```sql
-- Edge with constraints: only Person nodes can connect via FriendOf
CREATE TABLE FriendOf (
    CONSTRAINT EC_FriendOf CONNECTION (Person TO Person) ON DELETE CASCADE
) AS EDGE;

-- Multiple connection types on one edge table
CREATE TABLE Manages (
    CONSTRAINT EC_Manages CONNECTION (Person TO Person, Person TO Team)
) AS EDGE;
```

---

## Graph Queries with JSON

Node tables can store flexible or variable properties in a JSON column, enabling schema-on-read patterns while still supporting graph traversal via `MATCH`.

- Combine `JSON_VALUE` / `JSON_QUERY` with `MATCH` in the same query
- JSON columns are queried in the `SELECT` list or `WHERE` clause just like regular columns
- Useful when node types have heterogeneous attribute sets

```sql
-- Node table with JSON properties
CREATE TABLE Product (
    ProductID INT PRIMARY KEY,
    Name NVARCHAR(200),
    Attributes NVARCHAR(MAX)  -- JSON column
) AS NODE;

-- Query graph with JSON property filter
SELECT p.Name, JSON_VALUE(p.Attributes, '$.category') AS Category
FROM Product p, RecommendedWith r, Product p2
WHERE MATCH(p-(r)->p2)
AND JSON_VALUE(p.Attributes, '$.category') = 'Electronics';
```

---

## Performance Considerations for Graph Queries

Graph tables behave like regular tables for indexing and statistics — apply standard tuning principles in addition to graph-specific guidance.

- **Node tables:** index `$node_id` (system-maintained) and the business key used in `WHERE` filters
- **Edge tables:** index `$from_id` and `$to_id` pseudo-columns to accelerate traversal in both directions
- **SHORTEST_PATH on dense graphs:** always bound depth with `{1,N}` to avoid full-graph scans; unbounded `+` can be expensive
- **Statistics:** auto-update statistics apply to node and edge tables the same as heap/B-tree tables
- **Execution plans:** `MATCH` is translated into JOINs internally — `EXPLAIN` / actual execution plans show regular hash or nested-loop joins, not graph-specific operators

```sql
-- Index on edge endpoints for traversal performance
CREATE INDEX IX_FriendOf_From ON FriendOf($from_id);
CREATE INDEX IX_FriendOf_To ON FriendOf($to_id);

-- Index on node business key
CREATE INDEX IX_Person_Name ON Person(Name);
```

---

## Use Cases

- **Social networks**: Friend recommendations, influence analysis
- **Fraud detection**: Detect suspicious transaction rings or connected accounts
- **Knowledge graphs**: Linked entities for AI/RAG context retrieval
- **Bill of materials**: Component hierarchies with shared subcomponents
- **Recommendation engines**: "People who liked X also liked Y"

---

## Common Issues & Errors

| Issue | Cause | Resolution |
| :--- | :--- | :--- |
| `MATCH` fails | Graph tables not in FROM clause | All nodes and edges used in MATCH must be in the FROM clause |
| Edge insert fails | Wrong `$node_id` value | ==Always use subquery `(SELECT $node_id FROM ...)` to reference nodes== |
| Multiple MATCH patterns | Separate MATCH calls connected by AND | Use `AND MATCH(...)` for additional patterns |
| SHORTEST_PATH returns no rows | Source node has no outbound edges | Verify edge direction and that `FOR PATH` aliases are used correctly |
| Edge constraint violation | Inserting edge between disallowed node types | Check `CONNECTION` constraint definition; ensure source/target match allowed types |

---

## Best Practices

- Define edge constraints (`CONNECTION`) on all edge tables to enforce referential integrity at the schema level rather than in application code.
- Always index `$from_id` and `$to_id` on edge tables; without these indexes, traversal degrades to full table scans as graph size grows.
- Bound `SHORTEST_PATH` depth with `{1,N}` in production queries — unbounded `+` on dense graphs can cause runaway execution times.
- Use `FOR PATH` aliases only inside `SHORTEST_PATH`; do not mix `FOR PATH` aliases with regular node aliases in the same `MATCH` clause.
- Treat graph tables as first-class relational tables: apply column statistics, filtered indexes, and partitioning where appropriate.

---

## Exam Tips

> [!tip] Exam Tips
> - `MATCH` can only be used with graph tables (defined `AS NODE` or `AS EDGE`)
> - Arrow direction in `MATCH` corresponds to `$from_id` → `$to_id` in the edge table
> - `SHORTEST_PATH` requires the `FOR PATH` keyword on edge and node aliases
> - `LAST_NODE()` returns the final node in a `SHORTEST_PATH` traversal — use it to get the destination
> - `STRING_AGG(...) WITHIN GROUP (GRAPH PATH)` orders path values in traversal sequence
> - Graph tables can have additional user-defined columns just like regular tables
> - Edge constraints use `CONSTRAINT ... CONNECTION (NodeType TO NodeType)` syntax — know this for schema design questions

---

## Key Takeaways

- Node tables have `$node_id`; edge tables have `$edge_id`, `$from_id`, `$to_id`
- `MATCH` enables declarative graph traversal without recursive CTEs
- `SHORTEST_PATH` finds the minimum hop path between nodes; requires `FOR PATH` aliases
- Edge constraints enforce valid node-type pairings at the DDL level
- Index `$from_id` and `$to_id` on edge tables for performant traversal

---

## Related Topics

- [02-Specialized Tables](../01-database-objects/02-specialized-tables.md)
- [01-CTEs & Window Functions](./01-ctes-window-functions.md)

---

## Official Documentation

- [SQL Graph Architecture](https://learn.microsoft.com/en-us/sql/relational-databases/graphs/sql-graph-architecture)
- [MATCH (SQL Graph)](https://learn.microsoft.com/en-us/sql/t-sql/queries/match-sql-graph)
- [SHORTEST_PATH (SQL Graph)](https://learn.microsoft.com/en-us/sql/t-sql/queries/shortest-path-sql-graph)

---

**Practice Question**

You need to find all people within 3 hops of a specific person in a social graph. Which T-SQL feature enables this query?

A. Recursive CTE with a UNION ALL and hop counter
B. MATCH with SHORTEST_PATH using a + quantifier
C. A self-join with a JOIN depth of 3
D. OPENJSON to traverse a graph stored in JSON

> [!success]- Answer
> **B — MATCH with SHORTEST_PATH using a + quantifier**
>
> SHORTEST_PATH in graph queries uses the + quantifier (one or more hops) or {1,3} for bounded hops to traverse edges recursively. While recursive CTEs (A) can also traverse hierarchies, MATCH with SHORTEST_PATH is the native graph API for SQL Graph tables. OPENJSON (D) works for JSON-encoded trees but not SQL Graph node/edge tables.

---

**[← Previous](./03-regex-fuzzy-matching.md) | [↑ Back to Section](./README.md) | [Next →](./05-correlated-queries-error-handling.md)**
