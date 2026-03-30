---
title: Data Encryption
type: study-material
tags:
  - dp-800
  - encryption
  - always-encrypted
  - column-encryption
  - tde
---

# Data Encryption

## Overview

SQL Server provides multiple encryption layers: Transparent Data Encryption (TDE) for data at rest, Always Encrypted for client-side column-level encryption, and server-side column encryption using certificates and asymmetric keys.

## Transparent Data Encryption (TDE)

TDE encrypts database files at rest — transparent to applications, no code changes needed.

```sql
-- Enable TDE (Azure SQL has TDE enabled by default)
USE master;
CREATE MASTER KEY ENCRYPTION BY PASSWORD = 'StrongP@ssword123!';

CREATE CERTIFICATE TDECert
WITH SUBJECT = 'TDE Certificate';

USE MyDatabase;
CREATE DATABASE ENCRYPTION KEY
WITH ALGORITHM = AES_256
ENCRYPTION BY SERVER CERTIFICATE TDECert;

ALTER DATABASE MyDatabase SET ENCRYPTION ON;

-- Check TDE status
SELECT db_name(database_id) AS DatabaseName,
       encryption_state_desc,
       key_algorithm,
       key_length
FROM sys.dm_database_encryption_keys;
```

**TDE encryption states:**
| State | Description |
| :--- | :--- |
| 0 | No database encryption key, no encryption |
| 1 | Unencrypted |
| 2 | Encryption in progress |
| 3 | Encrypted |
| 4 | Key change in progress |
| 5 | Decryption in progress |

> Azure SQL Database and SQL Managed Instance have TDE enabled by default.

## Always Encrypted

Always Encrypted encrypts data **on the client side** — the database engine never sees plaintext. This protects against DBAs and cloud operators.

### Key Hierarchy

```text
Column Master Key (CMK)
└── Column Encryption Key (CEK)
    └── Encrypted column data
```

### Setting Up Always Encrypted

```sql
-- Step 1: Create Column Master Key (key stored in Windows Cert Store, Azure Key Vault, etc.)
CREATE COLUMN MASTER KEY MyCMK
WITH (
    KEY_STORE_PROVIDER_NAME = 'AZURE_KEY_VAULT',
    KEY_PATH = 'https://mykeyvault.vault.azure.net/keys/MyCMKKey/version'
);

-- Step 2: Create Column Encryption Key
CREATE COLUMN ENCRYPTION KEY MyCEK
WITH VALUES (
    COLUMN_MASTER_KEY = MyCMK,
    ALGORITHM = 'RSA_OAEP',
    ENCRYPTED_VALUE = 0x01700000... -- encrypted by the CMK
);

-- Step 3: Create table with encrypted columns
CREATE TABLE dbo.Patients (
    PatientId   int             NOT NULL PRIMARY KEY,
    -- DETERMINISTIC: allows equality comparisons (=, IN, JOIN)
    SSN         char(11)        COLLATE Latin1_General_BIN2
                                ENCRYPTED WITH (
                                    COLUMN_ENCRYPTION_KEY = MyCEK,
                                    ENCRYPTION_TYPE = DETERMINISTIC,
                                    ALGORITHM = 'AEAD_AES_256_CBC_HMAC_SHA_256'
                                ) NOT NULL,
    -- RANDOMIZED: more secure, no equality comparison possible
    Salary      money           ENCRYPTED WITH (
                                    COLUMN_ENCRYPTION_KEY = MyCEK,
                                    ENCRYPTION_TYPE = RANDOMIZED,
                                    ALGORITHM = 'AEAD_AES_256_CBC_HMAC_SHA_256'
                                ) NULL
);
```

### Encryption Types

| Type | Operations Supported | Security Level |
| :--- | :--- | :--- |
| **DETERMINISTIC** | `=`, `IN`, `JOIN`, `GROUP BY` | Lower (same plaintext = same ciphertext) |
| **RANDOMIZED** | None (value is opaque) | Higher (same plaintext = different ciphertext) |

### Querying Always Encrypted Columns

Client must have access to the CMK and use a driver with Always Encrypted enabled:

```csharp
// .NET connection string with Always Encrypted
"Server=...;Database=...;Column Encryption Setting=enabled;Authentication=Active Directory Integrated;"
```

```sql
-- T-SQL cannot directly read/write Always Encrypted columns
-- These queries only work from a client with CMK access:
SELECT * FROM dbo.Patients WHERE SSN = '123-45-6789';  -- works with DETERMINISTIC
```

## Server-Side Column Encryption

For less strict requirements (but still protects against SQL injection and unauthorized reads), use `ENCRYPTBYKEY` / `DECRYPTBYKEY`:

```sql
-- Create symmetric key
CREATE SYMMETRIC KEY MySymKey
WITH ALGORITHM = AES_256
ENCRYPTION BY CERTIFICATE MyCert;

-- Encrypt
OPEN SYMMETRIC KEY MySymKey DECRYPTION BY CERTIFICATE MyCert;

UPDATE dbo.Users
SET EncryptedPhone = ENCRYPTBYKEY(KEY_GUID('MySymKey'), Phone);

CLOSE SYMMETRIC KEY MySymKey;

-- Decrypt
OPEN SYMMETRIC KEY MySymKey DECRYPTION BY CERTIFICATE MyCert;
SELECT CONVERT(nvarchar(50), DECRYPTBYKEY(EncryptedPhone)) AS Phone
FROM dbo.Users;
CLOSE SYMMETRIC KEY MySymKey;
```

## Encryption Comparison

| Feature | TDE | Always Encrypted | Column Encryption |
| :--- | :--- | :--- | :--- |
| Protects | Data at rest (files) | Data from DBAs/server | Data in queries |
| Encryption side | Server | **Client** | Server |
| DBA can read | Yes | **No** | Yes (with key) |
| Application changes | None | Driver config | App code needed |
| Key location | Server / Azure Key Vault | **Client / Key Vault** | Server |

## Use Cases

- **TDE**: Compliance baseline for data at rest — healthcare, finance
- **Always Encrypted**: High-sensitivity columns (SSN, credit card) where DBAs must be excluded
- **Column Encryption**: Application-managed encryption with server-side storage

## Common Issues & Errors

| Error | Cause | Resolution |
| :--- | :--- | :--- |
| Cannot query encrypted column | Wrong encryption type or no CMK access | Use DETERMINISTIC for searchable; grant CMK access to app |
| TDE backup restore fails | Certificate not in target server | Backup and restore the TDE certificate first |
| Always Encrypted driver error | Driver doesn't support Always Encrypted | Use SqlClient with `Column Encryption Setting=enabled` |

## Exam Tips

- **Always Encrypted**: encryption happens client-side; SQL Server only sees ciphertext
- **DETERMINISTIC** allows `=` comparisons; **RANDOMIZED** allows no comparisons
- TDE protects files on disk — does NOT protect against a user with `SELECT` permission
- Always Encrypted requires the Column Master Key to be accessible from the client

## Key Takeaways

- TDE = at-rest file encryption (transparent, no app changes)
- Always Encrypted = client-side column encryption (DBAs see only ciphertext)
- Use DETERMINISTIC encryption when you need to search/filter; RANDOMIZED for maximum security

## Related Topics

- [02-Dynamic Data Masking & RLS](./02-dynamic-data-masking-rls.md)
- [03-Permissions & Access](./03-permissions-access.md)

## Official Documentation

- [Always Encrypted (SQL Server)](https://learn.microsoft.com/en-us/sql/relational-databases/security/encryption/always-encrypted-database-engine)
- [Transparent Data Encryption (TDE)](https://learn.microsoft.com/en-us/sql/relational-databases/security/encryption/transparent-data-encryption)
- [Column Encryption using Always Encrypted with Azure Key Vault](https://learn.microsoft.com/en-us/azure/azure-sql/database/always-encrypted-azure-key-vault-configure)

---

**[↑ Back to Section](./README.md) | [Next →](./02-dynamic-data-masking-rls.md)**
