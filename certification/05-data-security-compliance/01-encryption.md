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

> [!abstract]
> - Covers TDE (at rest, database-wide), Always Encrypted (in memory, column-level), and column-level encryption (manual)
> - The three encryption methods differ in threat model: who/what is the data protected from
> - Key exam topics: which encryption method for which threat, CMK/CEK hierarchy, TDE default-on behavior in Azure SQL

> [!tip] What the Exam Tests
> - **TDE**: protects at rest (stolen backup/disk); server sees plaintext; zero app changes; on by default in Azure SQL
> - **Always Encrypted**: server NEVER sees plaintext; CMK lives in key store (Azure Key Vault / HSM / Windows cert store), accessed only by the client driver; driver handles encrypt/decrypt; app must use Always Encrypted-aware driver
> - **Column-level** (`ENCRYPTBYKEY`): manual encrypt/decrypt in app or T-SQL; server sees plaintext; most flexible but most effort

---

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
| 0 | No DEK exists; no encryption |
| 1 | DEK exists but encryption not enabled |
| 2 | Encryption in progress |
| 3 | Encrypted |
| 4 | Key change in progress |
| 5 | Decryption in progress |

> Azure SQL Database and SQL Managed Instance have TDE enabled by default.

---

## Always Encrypted

**Always Encrypted** encrypts data on the client side — the database engine never sees plaintext. This protects against DBAs and cloud operators.

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
| **RANDOMIZED** | None (value is opaque) | ==Higher (same plaintext = different ciphertext)== |

> [!warning] Common Mistake
> TDE and Always Encrypted are often confused on the exam. TDE: server DOES see plaintext (it decrypts to run queries). Always Encrypted: server NEVER sees plaintext (encryption/decryption happens in the client driver). The key differentiator in exam scenarios is whether the database administrator (DBA) should be prevented from seeing the data.

> [!note] Mental model — Always Encrypted
> Think of Always Encrypted like sending your DBA a **locked briefcase**. They hold the briefcase (encrypted column), but the CMK (key) lives in your key store — Azure Key Vault, an HSM, or the Windows cert store. Only your client driver can use the CMK to unlock the CEK; the database engine never sees either in plaintext. The DBA can stack briefcases, ship them, back them up — but never look inside. **DETERMINISTIC** is like always using the same lock pattern so the DBA can sort briefcases (enabling equality compare). **RANDOMIZED** is a new lock each time — most secure, but the DBA can't tell two briefcases apart.

---

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

---

## Always Encrypted with Secure Enclaves

### Problem with Standard Always Encrypted

Standard Always Encrypted has a significant limitation: encrypted columns support only equality comparisons with deterministic encryption. Range queries (`<`, `>`, `BETWEEN`), `LIKE`, pattern matching, and in-place encryption are not possible because the server never sees plaintext.

### Solution: Secure Enclaves

A secure enclave is an isolated computation environment inside the database server where encrypted data can be processed without exposing plaintext to the broader database engine or DBAs.

Azure SQL Database uses **VBS (Virtualization Based Security)** enclaves.

### Supported Operations in Secure Enclaves

- Range queries: `<`, `>`, `<=`, `>=`, `BETWEEN`
- Pattern matching: `LIKE`, `IN`
- In-place encryption and re-encryption (no data movement needed)

### Connection Requirements

The client connection string must specify enclave attestation:

```text
Column Encryption Setting=Enabled; Attestation Protocol=HGS; Enclave Attestation Url=https://...
```

### Enclave Examples

```sql
-- Column encrypted with randomized encryption + enclave-enabled CEK
-- Can now support range queries via the secure enclave
SELECT PatientID, Name
FROM Patients
WHERE Age BETWEEN 30 AND 50;  -- works with enclave, would fail without

-- In-place encryption (no data movement needed)
ALTER TABLE Patients
ALTER COLUMN SSN NVARCHAR(11) ENCRYPTED WITH (
    ENCRYPTION_TYPE = RANDOMIZED,
    ALGORITHM = 'AEAD_AES_256_CBC_HMAC_SHA_256',
    COLUMN_ENCRYPTION_KEY = EnclaveCEK
) WITH (ONLINE = ON);
```

---

## Key Rotation Procedures

### Why Rotate Keys

- Compliance requirements (periodic rotation mandates)
- Suspected compromise of a key or key store
- Personnel changes (staff with key access leave the organization)

### Column Master Key Rotation

CMK rotation is a metadata-only operation coordinated between the client (with key access) and the server:

1. Add new CMK (provision in Azure Key Vault or cert store)
2. Re-encrypt all CEKs with the new CMK
3. Remove the old CMK's encryption of the CEKs
4. Drop the old CMK

### Column Encryption Key Rotation

CEK rotation requires re-encrypting the actual column data with the new CEK.

### Rotation Tools

- **SSMS**: Right-click CMK/CEK in Object Explorer > Rotate
- **PowerShell**: `Invoke-SqlColumnMasterKeyRotation`, `Complete-SqlColumnMasterKeyRotation`
- **Azure Key Vault**: Automatic rotation policies (triggers notification; manual re-wrap step still needed)

### Key Rotation SQL Metadata Steps

```sql
-- Step 1: Add new CMK (actual key in Azure Key Vault)
CREATE COLUMN MASTER KEY NewCMK
WITH (KEY_STORE_PROVIDER_NAME = 'AZURE_KEY_VAULT',
      KEY_PATH = 'https://mykeyvault.vault.azure.net/keys/NewCMK/version2');

-- Step 2: Create new CEK encrypted with new CMK
-- (encrypted_value generated by SSMS/PowerShell with access to both keys)
ALTER COLUMN ENCRYPTION KEY MyCEK
ADD VALUE (COLUMN_MASTER_KEY = NewCMK,
           ALGORITHM = 'RSA_OAEP',
           ENCRYPTED_VALUE = 0x...);

-- Step 3: Remove old CMK's encryption of the CEK
ALTER COLUMN ENCRYPTION KEY MyCEK
DROP VALUE (COLUMN_MASTER_KEY = OldCMK);

-- Step 4: Drop old CMK
DROP COLUMN MASTER KEY OldCMK;
```

---

## Transparent Data Encryption (TDE) — Certificate Backup

Backing up the TDE certificate is critical. If the certificate is lost, database backups become permanently unreadable.

- Back up the certificate with its private key to a secure, offsite location
- For on-premises and SQL Managed Instance: use `BACKUP CERTIFICATE`
- For Azure SQL Database: TDE certificate is managed by Microsoft by default, or use a customer-managed key (BYOK — Bring Your Own Key) via Azure Key Vault

```sql
-- Backup TDE certificate (on-premises or SQL MI)
BACKUP CERTIFICATE TDECert
TO FILE = 'C:\Backup\TDECert.cer'
WITH PRIVATE KEY (
    FILE = 'C:\Backup\TDECert_pk.pvk',
    ENCRYPTION BY PASSWORD = 'StrongBk*pPassword1!'
);
```

> Store the backup file and password separately. Both are required to restore on another server.

---

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

---

## Encryption Comparison Summary

| Feature | TDE | Always Encrypted | Column-Level Encryption (ENCRYPTBYKEY) |
| :--- | :--- | :--- | :--- |
| Protects against | Stolen disk/backup | DBA/privileged user access | Specific column data exposure |
| Key location | Database/server | Client application | Database (key in symmetric key) |
| Transparent to queries | Yes | Yes (with driver) | No (must call DECRYPTBYKEY) |
| Performance impact | Low (<5%) | Client-side overhead | Per-call overhead |
| Range query support | N/A | Enclave only | No |
| Exam relevance | Always Encrypted vs TDE distinction | Column-level use cases | Legacy approach |

---

## Use Cases

- **TDE**: Compliance baseline for data at rest — healthcare, finance
- **Always Encrypted**: High-sensitivity columns (SSN, credit card) where DBAs must be excluded
- **Always Encrypted + Enclaves**: When DBAs must be excluded AND range/LIKE queries are needed
- **Column Encryption**: Application-managed encryption with server-side storage

---

## Common Issues & Errors

| Error | Cause | Resolution |
| :--- | :--- | :--- |
| Cannot query encrypted column | Wrong encryption type or no CMK access | Use DETERMINISTIC for searchable; grant CMK access to app |
| TDE backup restore fails | Certificate not in target server | Backup and restore the TDE certificate first |
| Always Encrypted driver error | Driver doesn't support Always Encrypted | Use SqlClient with `Column Encryption Setting=enabled` |
| Range query fails on encrypted column | No secure enclave configured | ==Enable enclave-enabled CEK and configure attestation== |
| Key rotation fails mid-process | Both CMK values must coexist during rotation | Complete rotation before removing old CMK |

---

## Best Practices

- Always back up the TDE certificate immediately after creating it — before you need it
- Use Azure Key Vault for CMK storage; avoid Windows Certificate Store in production
- Prefer enclave-enabled CEKs for new Always Encrypted deployments to preserve query flexibility
- Rotate Column Master Keys at least annually or immediately upon suspected compromise
- Test Always Encrypted column queries from application code before deploying — T-SQL alone cannot verify driver compatibility

---

## Exam Tips

> [!tip] Exam Tips
> - **Always Encrypted**: encryption happens client-side; SQL Server only sees ciphertext
> - **DETERMINISTIC** allows `=` comparisons; **RANDOMIZED** allows no comparisons without a secure enclave
> - **Secure enclaves** unlock range queries and LIKE on RANDOMIZED encrypted columns
> - TDE protects files on disk — does NOT protect against a user with `SELECT` permission
> - Always Encrypted requires the Column Master Key to be accessible from the client
> - Losing the TDE certificate means losing access to all backups encrypted under it
> - CMK rotation is metadata-only; CEK rotation requires re-encrypting actual column data

---

## Key Takeaways

- TDE = at-rest file encryption (transparent, no app changes)
- Always Encrypted = client-side column encryption (DBAs see only ciphertext)
- Use DETERMINISTIC encryption when you need to search/filter; RANDOMIZED for maximum security
- Secure enclaves extend Always Encrypted to support range queries and LIKE on RANDOMIZED columns
- Back up TDE certificates — losing them makes database backups unrestorable

---

## Practice Question

A compliance requirement states that encrypted patient records must be searchable by date range (BETWEEN) without exposing plaintext to the database engine. Which Always Encrypted configuration satisfies this?

A. Deterministic encryption with a standard Column Encryption Key
B. Randomized encryption with a standard Column Encryption Key
C. Randomized encryption with an enclave-enabled Column Encryption Key
D. TDE with customer-managed keys in Azure Key Vault

> [!success]- Answer
> **C — Randomized encryption with an enclave-enabled Column Encryption Key**
>
> Standard Always Encrypted with randomized encryption cannot perform range queries. Secure enclaves allow the encrypted data to be processed inside an isolated computation environment on the server, enabling range queries (BETWEEN, <, >) while still keeping plaintext away from the database engine. Deterministic encryption (A) allows equality only, not ranges. TDE (D) protects data at rest but doesn't encrypt column values from DBAs.

---

## Related Topics

- [02-Dynamic Data Masking & RLS](./02-dynamic-data-masking-rls.md)
- [03-Permissions & Access](./03-permissions-access.md)

---

## Official Documentation

- [Always Encrypted (SQL Server)](https://learn.microsoft.com/en-us/sql/relational-databases/security/encryption/always-encrypted-database-engine)
- [Always Encrypted with Secure Enclaves](https://learn.microsoft.com/en-us/sql/relational-databases/security/encryption/always-encrypted-enclaves)
- [Transparent Data Encryption (TDE)](https://learn.microsoft.com/en-us/sql/relational-databases/security/encryption/transparent-data-encryption)
- [Column Encryption using Always Encrypted with Azure Key Vault](https://learn.microsoft.com/en-us/azure/azure-sql/database/always-encrypted-azure-key-vault-configure)
- [Rotate Always Encrypted Keys](https://learn.microsoft.com/en-us/sql/relational-databases/security/encryption/rotate-always-encrypted-keys-using-ssms)

---

**[↑ Back to Section](./data-security-compliance.md) | [Next →](./02-dynamic-data-masking-rls.md)**
