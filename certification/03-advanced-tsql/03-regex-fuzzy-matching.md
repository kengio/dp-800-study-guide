---
title: Regex and Fuzzy String Matching
type: study-material
tags:
  - dp-800
  - regex
  - fuzzy-matching
  - edit-distance
  - jaro-winkler
---

# Regex and Fuzzy String Matching

## Overview

SQL Server (and especially SQL databases in Microsoft Fabric) provide regex functions for pattern-based string matching and fuzzy string matching functions for similarity scoring — essential for data quality, deduplication, and AI-assisted search.

## Regex Functions

Regex functions follow POSIX-style regular expressions.

### REGEXP_LIKE — Pattern Test

```sql
-- Returns 1 if the string matches the pattern, 0 otherwise
SELECT REGEXP_LIKE('user@example.com', '^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$') AS IsValidEmail;
-- Returns: 1

-- Filter rows matching a pattern
SELECT * FROM dbo.Customers
WHERE REGEXP_LIKE(Phone, '^\+?[0-9\s\-()]{10,}$') = 1;
```

### REGEXP_REPLACE — Replace Patterns

```sql
-- Replace all non-alphanumeric characters with empty string
SELECT REGEXP_REPLACE('(123) 456-7890', '[^0-9]', '') AS DigitsOnly;
-- Returns: '1234567890'

-- Normalize whitespace
SELECT REGEXP_REPLACE('  too   many   spaces  ', '\s+', ' ') AS Normalized;
-- Returns: ' too many spaces '
```

### REGEXP_SUBSTR — Extract Substrings

```sql
-- Extract the first match
SELECT REGEXP_SUBSTR('Order #12345 for customer', '[0-9]+') AS OrderNumber;
-- Returns: '12345'

-- Extract with occurrence and position
SELECT REGEXP_SUBSTR('aa-bb-cc', '[a-z]+', 1, 2) AS SecondMatch;
-- Returns: 'bb'
```

### REGEXP_INSTR — Find Position

```sql
-- Returns the position of the first match (1-based)
SELECT REGEXP_INSTR('Hello World 123', '[0-9]+') AS NumberPosition;
-- Returns: 13
```

### REGEXP_COUNT — Count Matches

```sql
-- Count occurrences of pattern
SELECT REGEXP_COUNT('2025-01-15 and 2025-02-20', '[0-9]{4}-[0-9]{2}-[0-9]{2}') AS DateCount;
-- Returns: 2
```

### REGEXP_MATCHES — Return Match Table

```sql
-- Returns a table of all matches
SELECT match_value
FROM REGEXP_MATCHES('one two three', '[a-z]+');
-- Returns rows: 'one', 'two', 'three'
```

### REGEXP_SPLIT_TO_TABLE — Split by Pattern

```sql
-- Split string on delimiter pattern
SELECT value
FROM REGEXP_SPLIT_TO_TABLE('a,b,,c', ',+');
-- Returns rows: 'a', 'b', 'c'
```

## Fuzzy String Matching Functions

Fuzzy matching quantifies string similarity — useful for deduplication, data matching, and AI-assisted entity resolution.

### EDIT_DISTANCE (Levenshtein Distance)

Returns the minimum number of single-character edits (insertions, deletions, substitutions) to transform one string to another.

```sql
SELECT EDIT_DISTANCE('kitten', 'sitting');  -- Returns: 3
SELECT EDIT_DISTANCE('Microsoft', 'Microsift');  -- Returns: 1

-- Find similar product names (within 2 edits)
SELECT a.ProductId, a.Name, b.ProductId AS DupId, b.Name AS DupName,
       EDIT_DISTANCE(a.Name, b.Name) AS Distance
FROM dbo.Products a
JOIN dbo.Products b ON a.ProductId < b.ProductId
WHERE EDIT_DISTANCE(a.Name, b.Name) <= 2;
```

### EDIT_DISTANCE_SIMILARITY

Returns a similarity score from 0 (completely different) to 100 (identical) — normalized version of edit distance.

```sql
SELECT EDIT_DISTANCE_SIMILARITY('Microsoft', 'Microsift');  -- Returns: ~89

-- Find customers with similar names (>80% similar)
SELECT a.CustomerId, a.Name, b.CustomerId AS MatchId, b.Name AS MatchName,
       EDIT_DISTANCE_SIMILARITY(a.Name, b.Name) AS Similarity
FROM dbo.Customers a
JOIN dbo.Customers b ON a.CustomerId < b.CustomerId
WHERE EDIT_DISTANCE_SIMILARITY(a.Name, b.Name) > 80;
```

### JARO_WINKLER_DISTANCE

The Jaro-Winkler algorithm gives higher scores to strings that match from the beginning — well-suited for person names and short strings.

```sql
SELECT JARO_WINKLER_DISTANCE('MARTHA', 'MARHTA');   -- Returns: ~0.9611
SELECT JARO_WINKLER_DISTANCE('DWAYNE', 'DUANE');    -- Returns: ~0.8400
SELECT JARO_WINKLER_DISTANCE('John Smith', 'Jon Smith'); -- Returns: ~0.9878

-- Deduplication: find potential duplicate contacts
SELECT a.ContactId, a.FullName,
       b.ContactId AS MatchId, b.FullName AS MatchName,
       JARO_WINKLER_DISTANCE(a.FullName, b.FullName) AS Similarity
FROM dbo.Contacts a
JOIN dbo.Contacts b ON a.ContactId < b.ContactId
WHERE JARO_WINKLER_DISTANCE(a.FullName, b.FullName) > 0.92;
```

## Choosing the Right Function

| Scenario | Recommended Function |
| :--- | :--- |
| Validate email/phone format | `REGEXP_LIKE` |
| Extract numbers from text | `REGEXP_SUBSTR` |
| Clean/normalize data | `REGEXP_REPLACE` |
| Typo detection | `EDIT_DISTANCE` (absolute count) |
| Similarity scoring (%) | `EDIT_DISTANCE_SIMILARITY` |
| Person name matching | `JARO_WINKLER_DISTANCE` |
| Short identifier matching | `JARO_WINKLER_DISTANCE` |

## Use Cases

- **Data quality pipelines**: Identify misspelled values, normalize formats
- **Deduplication**: Find potential duplicate records before merging
- **Entity resolution**: Match records across datasets without common keys
- **AI data preparation**: Clean and normalize text before generating embeddings

## Common Issues & Errors

| Issue | Cause | Resolution |
| :--- | :--- | :--- |
| Regex functions not found | Not available in SQL Server; only in Fabric/Azure SQL | Check platform compatibility before using |
| Slow fuzzy join | Cross-join of large tables | Filter to candidate pairs first using cheaper predicates |
| Unexpected REGEXP_LIKE result | Case sensitivity | Use `i` flag for case-insensitive: `REGEXP_LIKE(col, pattern, 'i')` |

## Exam Tips

- Regex and fuzzy functions are primarily tested in the context of **SQL databases in Microsoft Fabric**
- `EDIT_DISTANCE` returns an absolute count; `EDIT_DISTANCE_SIMILARITY` returns a 0–100 percentage
- `JARO_WINKLER_DISTANCE` returns 0.0–1.0 (not 0–100) — note the different scale
- Use these for **data preparation before generating embeddings** (Domain 3 connection)

## Key Takeaways

- Regex functions provide POSIX-style pattern matching — more powerful than `LIKE`
- Fuzzy functions quantify string similarity — key for deduplication and entity resolution
- Combine regex (for format validation) with fuzzy matching (for similarity) in data quality pipelines

## Related Topics

- [02-JSON Functions](./02-json-functions.md)
- [04-Graph Queries](./04-graph-queries.md)
- [03-Chunking & Generation](../09-models-embeddings/03-chunking-generation.md)

## Official Documentation

- [REGEXP_LIKE (Transact-SQL)](https://learn.microsoft.com/en-us/sql/t-sql/functions/regexp-like-transact-sql)
- [EDIT_DISTANCE (Transact-SQL)](https://learn.microsoft.com/en-us/sql/t-sql/functions/edit-distance-transact-sql)
- [JARO_WINKLER_DISTANCE (Transact-SQL)](https://learn.microsoft.com/en-us/sql/t-sql/functions/jaro-winkler-distance-transact-sql)

---

**[← Previous](./02-json-functions.md) | [↑ Back to Section](./README.md) | [Next →](./04-graph-queries.md)**
