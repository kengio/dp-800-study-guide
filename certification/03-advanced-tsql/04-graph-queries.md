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

## Shortest Path

SQL Server supports `SHORTEST_PATH` for finding paths between nodes:

```sql
-- Find shortest path from Alice to any person (up to 5 hops)
SELECT
    src.Name AS Source,
    STRING_AGG(via.Name, '->') WITHIN GROUP (GRAPH PATH) AS Path,
    LAST_VALUE(via.Name) WITHIN GROUP (GRAPH PATH) AS Destination,
    COUNT(via.PersonId) WITHIN GROUP (GRAPH PATH) AS Hops
FROM
    dbo.Person AS src,
    dbo.friendOf FOR PATH AS f,
    dbo.Person FOR PATH AS via
WHERE MATCH(SHORTEST_PATH(src(-(f)->via){1,5}))
  AND src.Name = 'Alice';
```

## Use Cases

- **Social networks**: Friend recommendations, influence analysis
- **Fraud detection**: Detect suspicious transaction rings or connected accounts
- **Knowledge graphs**: Linked entities for AI/RAG context retrieval
- **Bill of materials**: Component hierarchies with shared subcomponents
- **Recommendation engines**: "People who liked X also liked Y"

## Common Issues & Errors

| Issue | Cause | Resolution |
| :--- | :--- | :--- |
| `MATCH` fails | Graph tables not in FROM clause | All nodes and edges used in MATCH must be in the FROM clause |
| Edge insert fails | Wrong `$node_id` value | Always use subquery `(SELECT $node_id FROM ...)` to reference nodes |
| Multiple MATCH patterns | Separate MATCH calls connected by AND | Use `AND MATCH(...)` for additional patterns |

## Exam Tips

- `MATCH` can only be used with graph tables (defined `AS NODE` or `AS EDGE`)
- Arrow direction in `MATCH` corresponds to `$from_id` → `$to_id` in the edge table
- `SHORTEST_PATH` requires the `FOR PATH` keyword on edge and node aliases
- Graph tables can have additional user-defined columns just like regular tables

## Key Takeaways

- Node tables have `$node_id`; edge tables have `$edge_id`, `$from_id`, `$to_id`
- `MATCH` enables declarative graph traversal without recursive CTEs
- `SHORTEST_PATH` finds the minimum hop path between nodes

## Related Topics

- [02-Specialized Tables](../01-database-objects/02-specialized-tables.md)
- [01-CTEs & Window Functions](./01-ctes-window-functions.md)

## Official Documentation

- [SQL Graph Architecture](https://learn.microsoft.com/en-us/sql/relational-databases/graphs/sql-graph-architecture)
- [MATCH (SQL Graph)](https://learn.microsoft.com/en-us/sql/t-sql/queries/match-sql-graph)
- [SHORTEST_PATH (SQL Graph)](https://learn.microsoft.com/en-us/sql/t-sql/queries/shortest-path-sql-graph)

---

**[← Previous](./03-regex-fuzzy-matching.md) | [↑ Back to Section](./README.md) | [Next →](./05-correlated-queries-error-handling.md)**
