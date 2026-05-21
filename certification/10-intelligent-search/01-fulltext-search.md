---
title: Full-Text Search
type: study-material
tags:
  - dp-800
  - full-text-search
  - fts
  - contains
  - freetext
---

# Full-Text Search

## Overview

Full-text search (FTS) enables linguistic searching of character-based data — matching words, phrases, proximity, and inflected forms. Unlike LIKE queries (which do character pattern matching), FTS uses an **inverted index** and understands language semantics (stems, synonyms, stop words). The key predicates are `CONTAINS` (precise term matching) and `FREETEXT` (natural language matching).

> [!abstract]
>
> - Covers full-text search in Azure SQL: CONTAINS, FREETEXT, CONTAINSTABLE, FREETEXTTABLE, and full-text indexes
> - Full-text search enables linguistic and proximity searches beyond LIKE pattern matching
> - Key exam topics: CONTAINS vs FREETEXT use cases, full-text index requirement, ranked results with TABLE variants

> [!tip] What the Exam Tests
>
> - `CONTAINS` = **precision**: exact terms, prefix (`"data*"`), proximity (`NEAR`), weighted terms (`ISABOUT`)
> - `FREETEXT` = **recall**: natural language query, inflections and synonyms, broader match
> - `CONTAINSTABLE` / `FREETEXTTABLE` return a table with a `RANK` column (0–1000) — use when you need ranked results or want to join with other tables

---

## Full-Text Catalogs and Indexes

### Creating a Full-Text Catalog

```sql
-- A full-text catalog is a logical container for full-text indexes
CREATE FULLTEXT CATALOG [ProductCatalog] AS DEFAULT;

-- Verify
SELECT * FROM sys.fulltext_catalogs;
```

### Creating a Full-Text Index

```sql
-- A full-text index requires:
-- 1. A unique, single-column, non-nullable index (usually the PK)
-- 2. A full-text catalog

-- Create full-text index on Products table
CREATE FULLTEXT INDEX ON dbo.Products (
    ProductName LANGUAGE 1033,       -- 1033 = English
    Description LANGUAGE 1033
)
KEY INDEX PK_Products
ON ProductCatalog
WITH (CHANGE_TRACKING = AUTO,        -- AUTO = SQL tracks changes to indexed data
      STOPLIST = SYSTEM);            -- Use system stop list

-- Verify
SELECT * FROM sys.fulltext_indexes;
SELECT * FROM sys.fulltext_index_columns;
```

### Change Tracking Options

| Option | Behavior |
| :--- | :--- |
| `AUTO` | ==SQL Server automatically updates the FTS index when rows change== |
| `MANUAL` | Updates only when you call `ALTER FULLTEXT INDEX ... START UPDATE POPULATION` |
| `OFF` | No change tracking; manual full population only |

### Population (Building the Index)

```sql
-- Start a full population (rebuild entire index)
ALTER FULLTEXT INDEX ON dbo.Products START FULL POPULATION;

-- Start an incremental population (only changed rows since last population)
ALTER FULLTEXT INDEX ON dbo.Products START INCREMENTAL POPULATION;

-- Check population status
SELECT FULLTEXTCATALOGPROPERTY('ProductCatalog', 'PopulateStatus') AS Status;
-- 0 = Idle, 1 = Full population in progress, 5 = Throttled

-- Check if full-text index is populated
SELECT OBJECTPROPERTYEX(OBJECT_ID('dbo.Products'), 'TableFulltextPopulateStatus');
```

---

## Stop Lists

Stop words (common words like "the", "and", "is") are excluded from the index:

```sql
-- Create a custom stop list
CREATE FULLTEXT STOPLIST [MyStopList] FROM SYSTEM STOPLIST;

-- Add custom stop words
ALTER FULLTEXT STOPLIST [MyStopList] ADD 'product' LANGUAGE 'English';
ALTER FULLTEXT STOPLIST [MyStopList] ADD 'item' LANGUAGE 'English';

-- Assign to an index
ALTER FULLTEXT INDEX ON dbo.Products SET STOPLIST = [MyStopList];

-- View stop words
SELECT * FROM sys.fulltext_stopwords WHERE stoplist_id =
    (SELECT stoplist_id FROM sys.fulltext_stoplists WHERE name = 'MyStopList');
```

---

## CONTAINS — Precise Search Predicate

`CONTAINS` searches for rows that match specific term criteria. Returns a boolean (used in WHERE clause).

### Simple Term Search

```sql
-- Find products containing the word "wireless"
SELECT ProductId, ProductName
FROM dbo.Products
WHERE CONTAINS(Description, 'wireless');

-- Search across multiple columns
SELECT ProductId, ProductName
FROM dbo.Products
WHERE CONTAINS((ProductName, Description), 'bluetooth');

-- Search all full-text indexed columns
SELECT ProductId, ProductName
FROM dbo.Products
WHERE CONTAINS(*, 'ergonomic');
```

### Prefix Term Search

```sql
-- Find words starting with "comput" (matches computer, computing, computational)
SELECT ProductId, ProductName
FROM dbo.Products
WHERE CONTAINS(Description, '"comput*"');

-- Multiple prefix terms
SELECT ProductId, ProductName
FROM dbo.Products
WHERE CONTAINS(Description, '"wire*" OR "blue*"');
```

### Phrase Search

```sql
-- Exact phrase match
SELECT ProductId, ProductName
FROM dbo.Products
WHERE CONTAINS(Description, '"noise cancelling"');

-- Phrase with OR
SELECT ProductId, ProductName
FROM dbo.Products
WHERE CONTAINS(Description, '"noise cancelling" OR "active noise"');
```

### Boolean Operators

```sql
-- AND: both terms must appear
SELECT ProductId, ProductName
FROM dbo.Products
WHERE CONTAINS(Description, 'wireless AND headphones');

-- OR: either term
SELECT ProductId, ProductName
FROM dbo.Products
WHERE CONTAINS(Description, 'wireless OR bluetooth');

-- AND NOT: first term but not second
SELECT ProductId, ProductName
FROM dbo.Products
WHERE CONTAINS(Description, 'headphones AND NOT "in-ear"');
```

### NEAR — Proximity Search

```sql
-- NEAR: terms within 50 words of each other (default proximity)
SELECT ProductId, ProductName
FROM dbo.Products
WHERE CONTAINS(Description, 'NEAR((wireless, headphones), 5)');
-- Terms within 5 words of each other

-- Ordered NEAR (first term must come before second)
SELECT ProductId, ProductName
FROM dbo.Products
WHERE CONTAINS(Description, 'NEAR((noise, cancelling), 3, TRUE)');
-- TRUE = ordered
```

### FORMSOF — Inflectional and Thesaurus Matching

```sql
-- FORMSOF INFLECTIONAL: matches inflected forms (run, runs, running, ran)
SELECT ProductId, ProductName
FROM dbo.Products
WHERE CONTAINS(Description, 'FORMSOF(INFLECTIONAL, "connect")');
-- Matches: connect, connects, connected, connecting, connection

-- FORMSOF THESAURUS: matches synonyms from the thesaurus file
SELECT ProductId, ProductName
FROM dbo.Products
WHERE CONTAINS(Description, 'FORMSOF(THESAURUS, "fast")');
-- Matches: fast, quick, rapid, speedy (depending on thesaurus configuration)
```

---

## FREETEXT — Natural Language Search

`FREETEXT` breaks the input string into words and searches for any of them and their linguistic variations. It is less precise than CONTAINS but more natural-language friendly.

```sql
-- Natural language search — finds rows about fast wireless audio
SELECT ProductId, ProductName
FROM dbo.Products
WHERE FREETEXT(Description, 'fast wireless audio headphones');

-- FREETEXT automatically:
-- 1. Removes stop words
-- 2. Finds inflected forms (connected → connect, connecting, connection)
-- 3. Expands to thesaurus synonyms (if thesaurus configured)
-- 4. Uses OR logic (any of the words can match)
```

---

## CONTAINSTABLE and FREETEXTTABLE — Ranked Results

These table-valued functions return matching rows with a `RANK` score (1–1000, higher = better match):

### CONTAINSTABLE

```sql
-- Get products matching "wireless headphones" with rank scores
SELECT
    p.ProductId,
    p.ProductName,
    p.Description,
    ct.[RANK] AS SearchRank
FROM CONTAINSTABLE(dbo.Products, Description, 'wireless AND headphones') AS ct
JOIN dbo.Products p ON p.ProductId = ct.[KEY]
ORDER BY ct.[RANK] DESC;
```

### FREETEXTTABLE

```sql
-- Natural language search with rankings
SELECT
    p.ProductId,
    p.ProductName,
    ftt.[RANK] AS SearchRank
FROM FREETEXTTABLE(dbo.Products, (ProductName, Description), 'comfortable wireless earbuds') AS ftt
JOIN dbo.Products p ON p.ProductId = ftt.[KEY]
WHERE ftt.[RANK] > 50  -- filter by minimum relevance
ORDER BY ftt.[RANK] DESC;
```

### Top N Results with FREETEXTTABLE

```sql
-- Get top 10 most relevant results
SELECT TOP 10
    p.ProductId,
    p.ProductName,
    ftt.[RANK]
FROM FREETEXTTABLE(dbo.Products, Description, 'wireless audio', LANGUAGE 1033, 10) AS ftt
JOIN dbo.Products p ON p.ProductId = ftt.[KEY]
ORDER BY ftt.[RANK] DESC;
-- The 4th parameter (10) limits results inside the FTS engine
```

---

## Language Support

```sql
-- Create full-text index with multiple languages
CREATE FULLTEXT INDEX ON dbo.Products (
    Name LANGUAGE 'English',
    DescriptionDE LANGUAGE 'German',
    DescriptionFR LANGUAGE 'French'
)
KEY INDEX PK_Products ON ProductCatalog;

-- List available language IDs
SELECT lcid, name FROM sys.fulltext_languages ORDER BY name;
-- Common: 1033=English, 1031=German, 1036=French, 1041=Japanese
```

---

## Use Cases

- **Product search**: Match product names and descriptions for keyword-based search in e-commerce
- **Document library search**: Find articles containing specific terms or phrases
- **Knowledge base**: Search FAQ or support articles using natural language queries
- **FREETEXTTABLE for ranking**: Return results ordered by relevance, not just presence of keywords

---

## Common Issues & Errors

| Issue | Cause | Fix |
| :--- | :--- | :--- |
| `No full-text index` error | FTS not enabled on the table | `CREATE FULLTEXT INDEX ON dbo.Products ...` |
| Query returns no results | Stop words excluded the search term | Check if term is in stop list; query `sys.fulltext_stopwords` |
| Index not up to date | CHANGE_TRACKING = MANUAL | Switch to AUTO or manually call `START UPDATE POPULATION` |
| FORMSOF THESAURUS returns nothing | Thesaurus file not configured | Edit the thesaurus XML file for the language |
| CONTAINS syntax error | Quotes missing around phrases | Phrase searches require double quotes: `'"noise cancelling"'` |

---

## Exam Tips

> [!tip] Exam Tips
>
> - `CONTAINS` returns a boolean match — use in WHERE clause; `CONTAINSTABLE` returns ranked results — use as a table
> - `FREETEXT` is for natural language; `CONTAINS` is for precise control (prefix, proximity, boolean)
> - **Stop words** can suppress expected results — if "product" is in the stop list, searching for "product" returns nothing
> - `CHANGE_TRACKING = AUTO` keeps the FTS index current; `MANUAL` requires explicit repopulation
> - `FORMSOF(INFLECTIONAL, ...)` — great for verb forms (search "run" finds "running", "ran", "runs")
> - `RANK` from CONTAINSTABLE/FREETEXTTABLE is 1–1000 — useful for relevance-based ordering

---

## Key Takeaways

- Full-text indexes require a full-text catalog and a unique key index
- `CONTAINS`/`CONTAINSTABLE` for precise term, prefix, phrase, proximity, and Boolean searches
- `FREETEXT`/`FREETEXTTABLE` for natural language searches that automatically handle variations
- Use `FREETEXTTABLE` when you need relevance-ranked results for search UIs

---

## Related Topics

- [02-Vector Search](./02-vector-search.md)
- [03-Hybrid Search & RRF](./03-hybrid-search-rrf.md)
- [03-Chunking & Generation](../09-models-embeddings/03-chunking-generation.md)

---

## Official Documentation

- [Full-Text Search (SQL Server)](https://learn.microsoft.com/en-us/sql/relational-databases/search/full-text-search)
- [CONTAINS (T-SQL)](https://learn.microsoft.com/en-us/sql/t-sql/queries/contains-transact-sql)
- [FREETEXTTABLE (T-SQL)](https://learn.microsoft.com/en-us/sql/relational-databases/system-functions/freetexttable-transact-sql)

---

**[↑ Back to Section](./intelligent-search.md) | [Next →](./02-vector-search.md)**
