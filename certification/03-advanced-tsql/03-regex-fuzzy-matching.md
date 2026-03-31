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

> [!abstract]
> - Covers pattern matching (LIKE, PATINDEX), phonetic matching (SOUNDEX, DIFFERENCE), and full-text search (CONTAINS, FREETEXT)
> - T-SQL lacks true regex — LIKE with wildcards is the native pattern tool; full-text search handles natural language
> - Key exam topics: CONTAINS vs FREETEXT use cases, full-text index requirement, PATINDEX return value

> [!tip] What the Exam Tests
> - `CONTAINS` = **precision** — exact terms, prefix terms, proximity (`NEAR`), weighted terms
> - `FREETEXT` = **recall** — natural language, broader match, no exact syntax control
> - Both `CONTAINS` and `FREETEXT` require a **full-text index** on the column — they will not work on a regular index

---

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

---

## Fuzzy String Matching Functions

Fuzzy matching quantifies string similarity — useful for deduplication, data matching, and AI-assisted entity resolution.

### EDIT_DISTANCE (Levenshtein Distance)

**Edit distance** returns the minimum number of single-character edits (insertions, deletions, substitutions) to transform one string to another.

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

> [!warning] Common Mistake
> CONTAINS and FREETEXT are not interchangeable. If the question asks for "natural language search that finds synonyms and inflections," use FREETEXT. If it asks for "exact phrase or proximity search," use CONTAINS. Both need a full-text index — forgetting this requirement is a common wrong answer.

---

## SOUNDEX and DIFFERENCE Functions

SOUNDEX and DIFFERENCE are built-in T-SQL functions available in SQL Server and Azure SQL — not limited to Fabric — making them broadly applicable for phonetic matching.

- **SOUNDEX(string)**: returns a 4-character phonetic code (one letter + three digits) based on how the string sounds in English
- **DIFFERENCE(string1, string2)**: compares the SOUNDEX codes of two strings and returns a score from 0 to 4, where 4 means most phonetically similar and 0 means least similar
- **Use case**: fuzzy matching on names where spelling varies (e.g., "Smith" vs "Smyth"), matching imported data with inconsistent romanization
- **Limitations**: English-centric algorithm; unreliable for non-Latin characters, non-English names, or languages with different phonetic rules

```sql
-- SOUNDEX examples
SELECT SOUNDEX('Smith'),   -- S530
       SOUNDEX('Smyth'),   -- S530 (same!)
       SOUNDEX('Schmidt'); -- S253

-- DIFFERENCE: 4 = most similar, 0 = least
SELECT DIFFERENCE('Smith', 'Smyth'),    -- 4
       DIFFERENCE('Smith', 'Brown'),    -- 1
       DIFFERENCE('Robert', 'Rupert');  -- 3

-- Find all customers whose name sounds like 'Johnson'
SELECT CustomerID, Name
FROM Customers
WHERE DIFFERENCE(Name, 'Johnson') >= 3;
```

---

## TRANSLATE Function

`TRANSLATE(string, from_chars, to_chars)` replaces each character in `from_chars` with the corresponding character at the same position in `to_chars` — a one-for-one character substitution across multiple characters in a single call.

**Difference from REPLACE**: `REPLACE` substitutes one substring at a time and requires chaining for multiple replacements. `TRANSLATE` handles multiple single-character substitutions simultaneously, making it cleaner for data normalization.

**Use case**: removing or standardizing special characters in phone numbers, addresses, or codes.

```sql
-- Replace multiple characters at once
SELECT TRANSLATE('(555) 123-4567', '()-', '   ');  -- '555  123 4567'

-- Normalize phone numbers
SELECT TRANSLATE(TRIM(Phone), '()- .', '     ')
FROM Customers;  -- removes formatting chars

-- Compare to REPLACE (requires chaining)
SELECT REPLACE(REPLACE(REPLACE('(555)-123', '(', ''), ')', ''), '-', '');
-- TRANSLATE is cleaner: TRANSLATE('(555)-123', '()-', '   ')
```

---

## Advanced LIKE Patterns

`LIKE` supports richer pattern syntax beyond `%` wildcards — useful for validating structured data formats directly in T-SQL.

| Pattern | Meaning | Example |
| :--- | :--- | :--- |
| `%` | Any string (0+ chars) | `'S%'` matches Smith, SQL |
| `_` | Any single character | `'S_ith'` matches Smith |
| `[abc]` | Any single char in set | `'[SB]mith'` matches Smith, Bmith |
| `[a-z]` | Any char in range | ==`'[A-Z]%'` matches uppercase start== |
| `[^abc]` | Any char NOT in set | `'[^0-9]%'` not starting with digit |

Use the `ESCAPE` clause to treat `%`, `_`, or `[` as literal characters. Use `COLLATE` to control case sensitivity independently of the column's default collation.

```sql
-- Find product codes: exactly 3 uppercase letters + 4 digits
SELECT ProductCode FROM Products
WHERE ProductCode LIKE '[A-Z][A-Z][A-Z][0-9][0-9][0-9][0-9]';

-- Escape the % character (searching for literal %)
SELECT Name FROM Products
WHERE Name LIKE '%50\%%' ESCAPE '\';  -- '50% off sale'

-- Case-sensitive LIKE
SELECT Name FROM Customers
WHERE Name LIKE 'a%' COLLATE Latin1_General_CS_AS;
```

---

## Unicode and Collation in String Matching

Collation controls how SQL Server compares and sorts character data — it affects `LIKE`, `=`, `ORDER BY`, and index usage.

- **NVARCHAR vs VARCHAR**: use the `N` prefix for Unicode string literals when matching `NVARCHAR` columns (`N'Smith'`); omitting it can cause implicit conversion and index scan instead of seek
- **Collation sensitivity suffixes**:
  - `CI` = case insensitive (default in most databases), `CS` = case sensitive
  - `AI` = accent insensitive, `AS` = accent sensitive
- **Common collations**: `Latin1_General_CI_AS` (typical default), `Latin1_General_CS_AS` (case-sensitive)
- **Index impact**: a `LIKE` predicate with a mismatched collation cannot use an index seek efficiently — always match the collation of the column

```sql
-- Same data, different collation behavior
SELECT Name FROM Customers WHERE Name = N'José' COLLATE Latin1_General_CI_AI;  -- matches Jose, José
SELECT Name FROM Customers WHERE Name = N'José' COLLATE Latin1_General_CS_AS;  -- exact match only
```

---

## Choosing the Right Function

| Scenario | Recommended Function |
| :--- | :--- |
| Validate email/phone format | `REGEXP_LIKE` |
| Extract numbers from text | `REGEXP_SUBSTR` |
| Clean/normalize data | `REGEXP_REPLACE` |
| Typo detection | `EDIT_DISTANCE` (absolute count) |
| Similarity scoring (%) | ==`EDIT_DISTANCE_SIMILARITY`== |
| Person name matching | `JARO_WINKLER_DISTANCE` |
| Short identifier matching | `JARO_WINKLER_DISTANCE` |
| Phonetic name matching | `SOUNDEX` / `DIFFERENCE` |
| Normalize separator chars | `TRANSLATE` |
| Structured format validation | `LIKE` with character classes |

---

## Use Cases

- **Data quality pipelines**: Identify misspelled values, normalize formats
- **Deduplication**: Find potential duplicate records before merging
- **Entity resolution**: Match records across datasets without common keys
- **AI data preparation**: Clean and normalize text before generating embeddings

---

## Common Issues & Errors

| Issue | Cause | Resolution |
| :--- | :--- | :--- |
| Regex functions not found | Not available in SQL Server; only in Fabric/Azure SQL | Check platform compatibility before using |
| Slow fuzzy join | Cross-join of large tables | Filter to candidate pairs first using cheaper predicates |
| Unexpected REGEXP_LIKE result | Case sensitivity | Use `i` flag for case-insensitive: `REGEXP_LIKE(col, pattern, 'i')` |
| SOUNDEX returns wrong matches | Non-English names | Use `EDIT_DISTANCE` or `JARO_WINKLER_DISTANCE` instead |
| LIKE scan instead of seek | Leading wildcard `'%text%'` | ==Use full-text search (`CONTAINS`) for substring searches on large tables== |

---

## Best Practices

- Prefer `EDIT_DISTANCE_SIMILARITY` over raw `EDIT_DISTANCE` for threshold comparisons — the normalized 0–100 score is length-independent
- Pre-filter candidate rows with a cheaper predicate (e.g., same first letter, same length range) before applying expensive fuzzy functions in a cross-join
- Use `TRANSLATE` instead of chained `REPLACE` calls when normalizing multiple single-character delimiters — it is more readable and executes in one pass
- Avoid leading-wildcard `LIKE '%text%'` on large tables; use full-text search (`CONTAINS`) for scalable substring matching
- Always match the collation of string literals to the target column to ensure index seeks are used; specify `COLLATE` explicitly when in doubt

---

## Exam Tips

> [!tip] Exam Tips
> - Regex and fuzzy functions are primarily tested in the context of **SQL databases in Microsoft Fabric**
> - `EDIT_DISTANCE` returns an absolute count; `EDIT_DISTANCE_SIMILARITY` returns a 0–100 percentage
> - `JARO_WINKLER_DISTANCE` returns 0.0–1.0 (not 0–100) — note the different scale
> - `SOUNDEX`/`DIFFERENCE` are standard T-SQL (not Fabric-only); `DIFFERENCE` score of 4 = most similar
> - `TRANSLATE` requires equal-length `from_chars` and `to_chars` strings — a length mismatch throws an error
> - Leading-wildcard `LIKE` always causes a full scan; the exam may test knowing that full-text search is the index-friendly alternative
> - Use these for **data preparation before generating embeddings** (Domain 3 connection)

---

## Key Takeaways

- Regex functions provide POSIX-style pattern matching — more powerful than `LIKE`
- Fuzzy functions quantify string similarity — key for deduplication and entity resolution
- `SOUNDEX`/`DIFFERENCE` offer a lightweight phonetic match available in all SQL Server editions
- `TRANSLATE` cleanly normalizes multi-character separators in a single function call
- Combine regex (for format validation) with fuzzy matching (for similarity) in data quality pipelines

---

## Practice Questions

**Practice Question**

A query uses `WHERE Name LIKE '%Smith%'` on a table with 1 million rows. The query is slow. Which alternative provides similar results while being more index-friendly?

A. Use SOUNDEX(Name) = SOUNDEX('Smith')
B. Use CHARINDEX('Smith', Name) > 0
C. Create a full-text index and use CONTAINS(Name, '"Smith*"')
D. Use TRANSLATE(Name, 'Smith', '     ') IS NULL

> [!success]- Answer
> **C — Create a full-text index and use CONTAINS(Name, '"Smith*"')**
>
> A leading wildcard `LIKE '%Smith%'` always causes a full table scan — no regular index can help. Full-text indexes invert the word-to-row mapping, enabling efficient word and prefix searches. SOUNDEX (A) handles phonetic matches but not substring matches, and is still a function-based scan. CHARINDEX (B) also causes a full scan. TRANSLATE (D) doesn't help find the substring.

---

## Related Topics

- [02-JSON Functions](./02-json-functions.md)
- [04-Graph Queries](./04-graph-queries.md)
- [03-Chunking & Generation](../09-models-embeddings/03-chunking-generation.md)

---

## Official Documentation

- [REGEXP_LIKE (Transact-SQL)](https://learn.microsoft.com/en-us/sql/t-sql/functions/regexp-like-transact-sql)
- [EDIT_DISTANCE (Transact-SQL)](https://learn.microsoft.com/en-us/sql/t-sql/functions/edit-distance-transact-sql)
- [JARO_WINKLER_DISTANCE (Transact-SQL)](https://learn.microsoft.com/en-us/sql/t-sql/functions/jaro-winkler-distance-transact-sql)
- [SOUNDEX (Transact-SQL)](https://learn.microsoft.com/en-us/sql/t-sql/functions/soundex-transact-sql)
- [TRANSLATE (Transact-SQL)](https://learn.microsoft.com/en-us/sql/t-sql/functions/translate-transact-sql)

---

**[← Previous](./02-json-functions.md) | [↑ Back to Section](./README.md) | [Next →](./04-graph-queries.md)**
